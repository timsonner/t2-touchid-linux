// SPDX-License-Identifier: GPL-2.0-only
/*
 * Research CLI for /dev/t2-sep-lab (in-session SEP mailbox/OOL probes).
 *
 * Build:
 *   cc -O2 -Wall -I src -o t2-sep-lab tools/t2-sep-lab.c
 * or: tools/build-t2-sep-lab.sh [/path/to/install]
 */
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

#include "t2_sep_transport_uapi.h"

static const char *errno_name(int err)
{
	if (err < 0)
		err = -err;
	switch (err) {
	case 0: return "OK";
	case EPERM: return "EPERM";
	case ENOENT: return "ENOENT";
	case EIO: return "EIO";
	case EAGAIN: return "EAGAIN";
	case ENOMEM: return "ENOMEM";
	case EACCES: return "EACCES";
	case EFAULT: return "EFAULT";
	case EBUSY: return "EBUSY";
	case EEXIST: return "EEXIST";
	case ENODEV: return "ENODEV";
	case EINVAL: return "EINVAL";
	case ENOTTY: return "ENOTTY";
	case EMSGSIZE: return "EMSGSIZE";
	case ENOSPC: return "ENOSPC";
	case ETIMEDOUT: return "ETIMEDOUT";
	case EPROTO: return "EPROTO";
	case EOVERFLOW: return "EOVERFLOW";
	case EREMOTEIO: return "EREMOTEIO";
	case EBADMSG: return "EBADMSG";
	case ERANGE: return "ERANGE";
	default: return "ERRNO";
	}
}

static void print_result(const char *op, int ioctl_ret, int32_t result)
{
	int err = ioctl_ret < 0 ? errno : (result < 0 ? -result : 0);

	if (ioctl_ret < 0)
		printf("%s: ioctl_failed errno=%d (%s)\n", op, errno,
		       errno_name(errno));
	else if (result < 0)
		printf("%s: result=%d (%s)\n", op, result, errno_name(result));
	else
		printf("%s: ok\n", op);
	(void)err;
}

static int parse_u32(const char *text, uint32_t *out)
{
	char *end = NULL;
	unsigned long long v;

	errno = 0;
	v = strtoull(text, &end, 0);
	if (errno || !end || *end || v > UINT32_MAX)
		return -1;
	*out = (uint32_t)v;
	return 0;
}

static int parse_u8(const char *text, uint8_t *out)
{
	uint32_t v;

	if (parse_u32(text, &v) || v > 0xff)
		return -1;
	*out = (uint8_t)v;
	return 0;
}

static int hex_nibble(char c)
{
	if (c >= '0' && c <= '9')
		return c - '0';
	if (c >= 'a' && c <= 'f')
		return c - 'a' + 10;
	if (c >= 'A' && c <= 'F')
		return c - 'A' + 10;
	return -1;
}

static int parse_hex(const char *text, unsigned char *buf, size_t cap,
		     size_t *out_len)
{
	size_t n = 0;
	const char *p = text;

	while (*p) {
		int hi, lo;

		while (*p == ' ' || *p == ':' || *p == '-')
			p++;
		if (!*p)
			break;
		hi = hex_nibble(*p++);
		if (hi < 0 || !*p)
			return -1;
		lo = hex_nibble(*p++);
		if (lo < 0)
			return -1;
		if (n >= cap)
			return -1;
		buf[n++] = (unsigned char)((hi << 4) | lo);
	}
	*out_len = n;
	return 0;
}

static void hexdump(const unsigned char *buf, size_t len)
{
	size_t i;

	for (i = 0; i < len; i++) {
		printf("%02x", buf[i]);
		if ((i + 1) % 16 == 0 || i + 1 == len)
			putchar('\n');
		else
			putchar(' ');
	}
	if (!len)
		putchar('\n');
}

static int open_lab(void)
{
	int fd;

	if (geteuid() != 0) {
		fprintf(stderr, "t2-sep-lab: root required\n");
		return -1;
	}
	fd = open("/dev/t2-sep-lab", O_RDWR | O_CLOEXEC);
	if (fd < 0) {
		perror("open /dev/t2-sep-lab");
		return -1;
	}
	return fd;
}

static int cmd_status(int fd)
{
	struct t2_sep_lab_ioc_status st;

	memset(&st, 0, sizeof(st));
	if (ioctl(fd, T2_SEP_LAB_IOC_STATUS, &st) < 0) {
		perror("T2_SEP_LAB_IOC_STATUS");
		return 1;
	}
	printf("inbox_status=%#x outbox_status=%#x\n",
	       st.inbox_status, st.outbox_status);
	printf("msi_inbox=%d msi_outbox=%d\n",
	       st.msi_inbox_count, st.msi_outbox_count);
	printf("ool_out_first_le32=%#x next_transaction=%u\n",
	       st.ool_out_first_le32, st.next_transaction);
	printf("flags=%#x (ool_in=%u ool_out=%u aks=%u acm=%u lab=%u)\n",
	       st.flags,
	       !!(st.flags & T2_SEP_LAB_F_OOL_IN_REG),
	       !!(st.flags & T2_SEP_LAB_F_OOL_OUT_REG),
	       !!(st.flags & T2_SEP_LAB_F_MISC_AKS),
	       !!(st.flags & T2_SEP_LAB_F_MISC_ACM),
	       !!(st.flags & T2_SEP_LAB_F_LAB));
	return 0;
}

static int cmd_raw(int fd, int argc, char **argv)
{
	struct t2_sep_lab_ioc_raw_mb raw;
	bool have_w0 = false, have_w1 = false, have_w2 = false;
	bool wait_reply = true;
	int i;

	memset(&raw, 0, sizeof(raw));
	raw.timeout_ms = 5000;
	raw.flags = T2_SEP_LAB_RAW_F_WAIT_REPLY;

	for (i = 0; i < argc; i++) {
		if (!strcmp(argv[i], "--w0") && i + 1 < argc) {
			if (parse_u32(argv[++i], &raw.word[0]))
				goto bad;
			have_w0 = true;
		} else if (!strcmp(argv[i], "--w1") && i + 1 < argc) {
			if (parse_u32(argv[++i], &raw.word[1]))
				goto bad;
			have_w1 = true;
		} else if (!strcmp(argv[i], "--w2") && i + 1 < argc) {
			if (parse_u32(argv[++i], &raw.word[2]))
				goto bad;
			have_w2 = true;
		} else if (!strcmp(argv[i], "--timeout-ms") && i + 1 < argc) {
			if (parse_u32(argv[++i], &raw.timeout_ms))
				goto bad;
		} else if (!strcmp(argv[i], "--no-wait")) {
			wait_reply = false;
		} else if (!strcmp(argv[i], "--accept-any")) {
			raw.flags |= T2_SEP_LAB_RAW_F_ACCEPT_ANY_ENDPOINT;
		} else {
			fprintf(stderr, "unknown raw arg: %s\n", argv[i]);
			return 1;
		}
	}
	if (!have_w0 || !have_w1 || !have_w2) {
		fprintf(stderr, "raw requires --w0 --w1 --w2\n");
		return 1;
	}
	if (!wait_reply)
		raw.flags &= ~T2_SEP_LAB_RAW_F_WAIT_REPLY;
	else
		raw.flags |= T2_SEP_LAB_RAW_F_WAIT_REPLY;

	if (ioctl(fd, T2_SEP_LAB_IOC_RAW_MB, &raw) < 0) {
		print_result("raw", -1, 0);
		return 1;
	}
	print_result("raw", 0, raw.result);
	printf("tx: %08x %08x %08x\n", raw.word[0], raw.word[1], raw.word[2]);
	if (raw.flags & T2_SEP_LAB_RAW_F_WAIT_REPLY)
		printf("rx: %08x %08x %08x %08x\n",
		       raw.reply_word[0], raw.reply_word[1],
		       raw.reply_word[2], raw.reply_word[3]);
	return raw.result ? 1 : 0;
bad:
	fprintf(stderr, "invalid numeric argument\n");
	return 1;
}

static int cmd_ool_write(int fd, int argc, char **argv)
{
	struct t2_sep_lab_ioc_ool ool;
	unsigned char *buf = NULL;
	size_t len = 0;
	uint32_t offset = 0;
	bool have_offset = false;
	const char *file = NULL;
	const char *hex = NULL;
	int i, ret = 1;

	memset(&ool, 0, sizeof(ool));
	for (i = 0; i < argc; i++) {
		if (!strcmp(argv[i], "--offset") && i + 1 < argc) {
			if (parse_u32(argv[++i], &offset))
				goto bad;
			have_offset = true;
		} else if (!strcmp(argv[i], "--file") && i + 1 < argc) {
			file = argv[++i];
		} else if (!strcmp(argv[i], "--hex") && i + 1 < argc) {
			hex = argv[++i];
		} else {
			fprintf(stderr, "unknown ool-write arg: %s\n", argv[i]);
			return 1;
		}
	}
	if (!have_offset || (!file && !hex) || (file && hex)) {
		fprintf(stderr,
			"ool-write needs --offset N and exactly one of --file/--hex\n");
		return 1;
	}
	if (file) {
		FILE *f = fopen(file, "rb");
		long sz;

		if (!f) {
			perror("open file");
			return 1;
		}
		if (fseek(f, 0, SEEK_END) || (sz = ftell(f)) < 0 ||
		    fseek(f, 0, SEEK_SET)) {
			perror("size file");
			fclose(f);
			return 1;
		}
		if (sz > T2_SEP_LAB_OOL_SIZE) {
			fprintf(stderr, "file too large\n");
			fclose(f);
			return 1;
		}
		buf = malloc((size_t)sz);
		if (!buf || fread(buf, 1, (size_t)sz, f) != (size_t)sz) {
			perror("read file");
			free(buf);
			fclose(f);
			return 1;
		}
		fclose(f);
		len = (size_t)sz;
	} else {
		buf = malloc(T2_SEP_LAB_OOL_SIZE);
		if (!buf) {
			perror("malloc");
			return 1;
		}
		if (parse_hex(hex, buf, T2_SEP_LAB_OOL_SIZE, &len)) {
			fprintf(stderr, "invalid --hex\n");
			free(buf);
			return 1;
		}
	}

	ool.offset = offset;
	ool.length = (uint32_t)len;
	ool.direction = T2_SEP_LAB_OOL_DIR_WRITE;
	ool.user_buf = (uintptr_t)buf;
	if (ioctl(fd, T2_SEP_LAB_IOC_OOL, &ool) < 0) {
		perror("T2_SEP_LAB_IOC_OOL write");
		goto out;
	}
	printf("ool-write: ok offset=%u length=%u\n", offset, ool.length);
	ret = 0;
out:
	free(buf);
	return ret;
bad:
	fprintf(stderr, "invalid numeric argument\n");
	return 1;
}

static int cmd_ool_read(int fd, int argc, char **argv)
{
	struct t2_sep_lab_ioc_ool ool;
	unsigned char *buf = NULL;
	uint32_t offset = 0, length = 0;
	bool have_offset = false, have_length = false;
	const char *out_path = NULL;
	int i, ret = 1;

	memset(&ool, 0, sizeof(ool));
	for (i = 0; i < argc; i++) {
		if (!strcmp(argv[i], "--offset") && i + 1 < argc) {
			if (parse_u32(argv[++i], &offset))
				goto bad;
			have_offset = true;
		} else if (!strcmp(argv[i], "--length") && i + 1 < argc) {
			if (parse_u32(argv[++i], &length))
				goto bad;
			have_length = true;
		} else if (!strcmp(argv[i], "--out") && i + 1 < argc) {
			out_path = argv[++i];
		} else {
			fprintf(stderr, "unknown ool-read arg: %s\n", argv[i]);
			return 1;
		}
	}
	if (!have_offset || !have_length) {
		fprintf(stderr, "ool-read needs --offset N --length N\n");
		return 1;
	}
	buf = calloc(1, length ? length : 1);
	if (!buf) {
		perror("malloc");
		return 1;
	}
	ool.offset = offset;
	ool.length = length;
	ool.direction = T2_SEP_LAB_OOL_DIR_READ;
	ool.user_buf = (uintptr_t)buf;
	if (ioctl(fd, T2_SEP_LAB_IOC_OOL, &ool) < 0) {
		perror("T2_SEP_LAB_IOC_OOL read");
		goto out;
	}
	printf("ool-read: ok offset=%u length=%u\n", offset, length);
	if (out_path) {
		FILE *f = fopen(out_path, "wb");

		if (!f || fwrite(buf, 1, length, f) != length) {
			perror("write out");
			if (f)
				fclose(f);
			goto out;
		}
		fclose(f);
	} else {
		hexdump(buf, length);
	}
	ret = 0;
out:
	free(buf);
	return ret;
bad:
	fprintf(stderr, "invalid numeric argument\n");
	return 1;
}

static int cmd_ool_clear(int fd)
{
	struct t2_sep_lab_ioc_ool ool;

	memset(&ool, 0, sizeof(ool));
	ool.direction = T2_SEP_LAB_OOL_DIR_ZERO;
	if (ioctl(fd, T2_SEP_LAB_IOC_OOL, &ool) < 0) {
		perror("T2_SEP_LAB_IOC_OOL clear");
		return 1;
	}
	printf("ool-clear: ok\n");
	return 0;
}

static int cmd_ep0(int fd, int argc, char **argv)
{
	struct t2_sep_lab_ioc_ep0 ep0;
	bool have_ep = false, have_op = false, have_tag = false;
	bool have_size = false, have_dma = false;
	int i;

	memset(&ep0, 0, sizeof(ep0));
	for (i = 0; i < argc; i++) {
		if (!strcmp(argv[i], "--endpoint") && i + 1 < argc) {
			if (parse_u8(argv[++i], &ep0.target_endpoint))
				goto bad;
			have_ep = true;
		} else if (!strcmp(argv[i], "--opcode") && i + 1 < argc) {
			if (parse_u8(argv[++i], &ep0.opcode))
				goto bad;
			have_op = true;
		} else if (!strcmp(argv[i], "--tag") && i + 1 < argc) {
			if (parse_u8(argv[++i], &ep0.tag))
				goto bad;
			have_tag = true;
		} else if (!strcmp(argv[i], "--size") && i + 1 < argc) {
			if (parse_u32(argv[++i], &ep0.size))
				goto bad;
			have_size = true;
		} else if (!strcmp(argv[i], "--dma") && i + 1 < argc) {
			const char *s = argv[++i];

			if (!strcmp(s, "in"))
				ep0.dma_sel = T2_SEP_LAB_DMA_OOL_IN;
			else if (!strcmp(s, "out"))
				ep0.dma_sel = T2_SEP_LAB_DMA_OOL_OUT;
			else if (!strcmp(s, "acm-in"))
				ep0.dma_sel = T2_SEP_LAB_DMA_ACM_OOL_IN;
			else if (!strcmp(s, "acm-out"))
				ep0.dma_sel = T2_SEP_LAB_DMA_ACM_OOL_OUT;
			else {
				fprintf(stderr, "dma must be in|out|acm-in|acm-out\n");
				return 1;
			}
			have_dma = true;
		} else {
			fprintf(stderr, "unknown ep0 arg: %s\n", argv[i]);
			return 1;
		}
	}
	if (!have_ep || !have_op || !have_tag || !have_size || !have_dma) {
		fprintf(stderr,
			"ep0 needs --endpoint --opcode --tag --size --dma\n");
		return 1;
	}
	if (ioctl(fd, T2_SEP_LAB_IOC_EP0, &ep0) < 0) {
		print_result("ep0", -1, 0);
		return 1;
	}
	print_result("ep0", 0, ep0.result);
	printf("endpoint=%u opcode=%u tag=%u size=%u dma_sel=%u\n",
	       ep0.target_endpoint, ep0.opcode, ep0.tag, ep0.size, ep0.dma_sel);
	return ep0.result ? 1 : 0;
bad:
	fprintf(stderr, "invalid numeric argument\n");
	return 1;
}

static int cmd_aks(int fd, int argc, char **argv)
{
	struct t2_sep_lab_ioc_aks aks;
	unsigned char body[T2_SEP_LAB_AKS_MAX_BODY_SIZE];
	unsigned char *response = NULL;
	size_t body_len = 0;
	uint8_t op = 0, ver = 2;
	bool have_op = false, have_ver = false;
	bool zero_time = false, skip_digest = false, accept_any = false;
	uint32_t timeout_ms = 30000;
	uint32_t resp_cap = 4096;
	const char *body_hex = NULL;
	int i, ret = 1;

	memset(&aks, 0, sizeof(aks));
	memset(body, 0, sizeof(body));
	for (i = 0; i < argc; i++) {
		if (!strcmp(argv[i], "--op") && i + 1 < argc) {
			if (parse_u8(argv[++i], &op))
				goto bad;
			have_op = true;
		} else if (!strcmp(argv[i], "--ver") && i + 1 < argc) {
			if (parse_u8(argv[++i], &ver))
				goto bad;
			have_ver = true;
		} else if (!strcmp(argv[i], "--zero-time")) {
			zero_time = true;
		} else if (!strcmp(argv[i], "--skip-digest")) {
			skip_digest = true;
		} else if (!strcmp(argv[i], "--accept-any-ep7")) {
			accept_any = true;
		} else if (!strcmp(argv[i], "--timeout-ms") && i + 1 < argc) {
			if (parse_u32(argv[++i], &timeout_ms))
				goto bad;
		} else if (!strcmp(argv[i], "--body-hex") && i + 1 < argc) {
			body_hex = argv[++i];
		} else if (!strcmp(argv[i], "--response-capacity") &&
			   i + 1 < argc) {
			if (parse_u32(argv[++i], &resp_cap))
				goto bad;
		} else {
			fprintf(stderr, "unknown aks arg: %s\n", argv[i]);
			return 1;
		}
	}
	if (!have_op || !have_ver) {
		fprintf(stderr, "aks needs --op N --ver 1|2\n");
		return 1;
	}
	if (body_hex) {
		if (parse_hex(body_hex, body, sizeof(body), &body_len)) {
			fprintf(stderr, "invalid --body-hex\n");
			return 1;
		}
	}
	if (resp_cap > T2_SEP_LAB_AKS_MAX_BODY_SIZE)
		resp_cap = T2_SEP_LAB_AKS_MAX_BODY_SIZE;
	response = calloc(1, resp_cap ? resp_cap : 1);
	if (!response) {
		perror("malloc");
		return 1;
	}

	aks.operation = op;
	aks.header_ver = ver;
	aks.zero_usec_time = zero_time;
	aks.skip_digest = skip_digest;
	aks.accept_any_ep7 = accept_any;
	aks.timeout_ms = timeout_ms;
	aks.request_body_len = (uint32_t)body_len;
	aks.request_body = body_len ? (uintptr_t)body : 0;
	aks.response_capacity = resp_cap;
	aks.response = (uintptr_t)response;

	if (ioctl(fd, T2_SEP_LAB_IOC_AKS, &aks) < 0) {
		print_result("aks", -1, 0);
		goto out;
	}
	print_result("aks", 0, aks.result);
	printf("op=%#x ver=%u sep_status=%d response_length=%u\n",
	       aks.operation, aks.header_ver, aks.sep_status,
	       aks.response_length);
	printf("reply: %08x %08x %08x %08x\n",
	       aks.reply_word[0], aks.reply_word[1],
	       aks.reply_word[2], aks.reply_word[3]);
	if (aks.response_length && aks.result == 0)
		hexdump(response, aks.response_length);
	ret = aks.result ? 1 : 0;
out:
	free(response);
	return ret;
bad:
	fprintf(stderr, "invalid numeric argument\n");
	return 1;
}

static void usage(const char *argv0)
{
	fprintf(stderr,
		"Usage:\n"
		"  %s status\n"
		"  %s raw --w0 0x.. --w1 0x.. --w2 0x.. [--timeout-ms N] [--no-wait] [--accept-any]\n"
		"  %s ool-write --offset N --file path | --hex ...\n"
		"  %s ool-read --offset N --length N [--out path]\n"
		"  %s ool-clear\n"
		"  %s ep0 --endpoint N --opcode N --tag N --size N --dma in|out|acm-in|acm-out\n"
		"  %s aks --op 0x4d --ver 2 [--zero-time] [--skip-digest] [--accept-any-ep7]\n"
		"         [--body-hex ...] [--timeout-ms N] [--response-capacity N]\n",
		argv0, argv0, argv0, argv0, argv0, argv0, argv0);
}

int main(int argc, char **argv)
{
	int fd, rc;

	if (argc < 2) {
		usage(argv[0]);
		return 1;
	}
	fd = open_lab();
	if (fd < 0)
		return 1;

	if (!strcmp(argv[1], "status"))
		rc = cmd_status(fd);
	else if (!strcmp(argv[1], "raw"))
		rc = cmd_raw(fd, argc - 2, argv + 2);
	else if (!strcmp(argv[1], "ool-write"))
		rc = cmd_ool_write(fd, argc - 2, argv + 2);
	else if (!strcmp(argv[1], "ool-read"))
		rc = cmd_ool_read(fd, argc - 2, argv + 2);
	else if (!strcmp(argv[1], "ool-clear"))
		rc = cmd_ool_clear(fd);
	else if (!strcmp(argv[1], "ep0"))
		rc = cmd_ep0(fd, argc - 2, argv + 2);
	else if (!strcmp(argv[1], "aks"))
		rc = cmd_aks(fd, argc - 2, argv + 2);
	else {
		usage(argv[0]);
		rc = 1;
	}
	close(fd);
	return rc;
}
