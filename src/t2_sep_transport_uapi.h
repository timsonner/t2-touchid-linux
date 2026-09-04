/* SPDX-License-Identifier: GPL-2.0-only WITH Linux-syscall-note */
#ifndef T2_SEP_TRANSPORT_UAPI_H
#define T2_SEP_TRANSPORT_UAPI_H

#include <linux/ioctl.h>
#include <linux/types.h>

#define T2_AKS_IOC_MAGIC 0xa7

struct t2_aks_ioc_exchange {
	__u8 operation;
	__s8 sep_status;
	__u8 reserved0[2];
	__u32 request_length;
	__u32 response_capacity;
	__u32 response_length;
	__u64 request;
	__u64 response;
};

#define T2_AKS_IOC_EXCHANGE \
	_IOWR(T2_AKS_IOC_MAGIC, 0, struct t2_aks_ioc_exchange)

#define T2_ACM_IOC_MAGIC 0xac

struct t2_acm_ioc_exchange {
	__u8 request_code;
	__u8 reserved0[3];
	__u32 request_length;
	__u32 response_capacity;
	__u32 response_length;
	__u32 request_info;
	__u32 response_info;
	__u64 generation;
	__u64 request;
	__u64 response;
};

struct t2_acm_ioc_info {
	__u64 generation;
	__u32 capacity;
	__u32 flags;
};

#define T2_ACM_INFO_F_POISONED (1U << 0)

#define T2_ACM_IOC_EXCHANGE \
	_IOWR(T2_ACM_IOC_MAGIC, 0, struct t2_acm_ioc_exchange)
#define T2_ACM_IOC_GET_INFO \
	_IOR(T2_ACM_IOC_MAGIC, 1, struct t2_acm_ioc_info)

/*
 * Research-only in-session SEP lab (/dev/t2-sep-lab).
 * Stays available even when AKS capability negotiation fails.
 */
#define T2_SEP_LAB_IOC_MAGIC		0xa8

/* Matches driver T2_SEP_OOL_SIZE / body room under a V2 AKS envelope. */
#define T2_SEP_LAB_OOL_SIZE		0x4000
#define T2_SEP_LAB_AKS_V2_WIRE_SIZE	(4 + 0x50)
#define T2_SEP_LAB_AKS_MAX_BODY_SIZE \
	(T2_SEP_LAB_OOL_SIZE - T2_SEP_LAB_AKS_V2_WIRE_SIZE)

#define T2_SEP_LAB_F_OOL_IN_REG		(1U << 0)
#define T2_SEP_LAB_F_OOL_OUT_REG	(1U << 1)
#define T2_SEP_LAB_F_MISC_AKS		(1U << 2)
#define T2_SEP_LAB_F_MISC_ACM		(1U << 3)
#define T2_SEP_LAB_F_LAB		(1U << 4)

#define T2_SEP_LAB_RAW_F_WAIT_REPLY		(1U << 0)
#define T2_SEP_LAB_RAW_F_ACCEPT_ANY_ENDPOINT	(1U << 1)

#define T2_SEP_LAB_OOL_DIR_WRITE	0 /* user → ool_in */
#define T2_SEP_LAB_OOL_DIR_READ		1 /* ool_out → user */
#define T2_SEP_LAB_OOL_DIR_ZERO		2 /* zero both ool_in/out */

#define T2_SEP_LAB_DMA_OOL_IN		0
#define T2_SEP_LAB_DMA_OOL_OUT		1
#define T2_SEP_LAB_DMA_ACM_OOL_IN	2
#define T2_SEP_LAB_DMA_ACM_OOL_OUT	3

struct t2_sep_lab_ioc_status {
	__u32 inbox_status;
	__u32 outbox_status;
	__s32 msi_inbox_count;
	__s32 msi_outbox_count;
	__u32 ool_out_first_le32;
	__u8 next_transaction;
	__u8 reserved0[3];
	__u32 flags;
};

struct t2_sep_lab_ioc_raw_mb {
	__u32 word[3];
	__u32 timeout_ms;
	__u32 flags;
	__u32 reply_word[4];
	__s32 result;
};

struct t2_sep_lab_ioc_ool {
	__u32 offset;
	__u32 length;
	__u32 direction;
	__u32 reserved0;
	__u64 user_buf;
};

struct t2_sep_lab_ioc_ep0 {
	__u8 target_endpoint;
	__u8 opcode;
	__u8 tag;
	__u8 dma_sel;
	__u32 size;
	__s32 result;
	__u32 reserved0;
};

struct t2_sep_lab_ioc_aks {
	__u8 operation;
	__u8 header_ver;
	__u8 zero_usec_time;
	__u8 skip_digest;
	__u8 accept_any_ep7;
	__u8 reserved0[3];
	__u32 timeout_ms;
	__u32 request_body_len;
	__u32 response_capacity;
	__u32 response_length;
	__u64 request_body;
	__u64 response;
	__s8 sep_status;
	__u8 reserved1[3];
	__u32 reply_word[4];
	__s32 result;
};

#define T2_SEP_LAB_IOC_STATUS \
	_IOR(T2_SEP_LAB_IOC_MAGIC, 0, struct t2_sep_lab_ioc_status)
#define T2_SEP_LAB_IOC_RAW_MB \
	_IOWR(T2_SEP_LAB_IOC_MAGIC, 1, struct t2_sep_lab_ioc_raw_mb)
#define T2_SEP_LAB_IOC_OOL \
	_IOWR(T2_SEP_LAB_IOC_MAGIC, 2, struct t2_sep_lab_ioc_ool)
#define T2_SEP_LAB_IOC_EP0 \
	_IOWR(T2_SEP_LAB_IOC_MAGIC, 3, struct t2_sep_lab_ioc_ep0)
#define T2_SEP_LAB_IOC_AKS \
	_IOWR(T2_SEP_LAB_IOC_MAGIC, 4, struct t2_sep_lab_ioc_aks)

#endif
