#!/usr/bin/env swift
// SPDX-License-Identifier: GPL-2.0-only
//
// Read-only Catacomb archive fixture check, macOS side.
//
// Answers the cross-OS gate in enrollment_research/PROTOCOL_LEDGER.md: does the
// matching macOS decoder accept this archive? It never calls loadCatacomb,
// save, delete, or any biometric command, and it prints no UUIDs, no
// identity names and no secure-blob bytes -- only counts, key names,
// classes and hashes.
//
// Run it on a *copy* of a component, never on /Library/Catacomb itself:
//
//   cp /Library/Catacomb/<uuid>/user_000001f5.cat /tmp/copy.cat
//   ./tools/catacomb-decode-fixture.swift /tmp/copy.cat
//
// The first invocation compiles through swiftc and takes a minute; later
// ones are quick.

import Foundation
import CryptoKit
import Darwin

_ = dlopen("/System/Library/PrivateFrameworks/BiometricKit.framework/BiometricKit", RTLD_NOW)

func die(_ message: String) -> Never {
    FileHandle.standardError.write(("error: " + message + "\n").data(using: .utf8)!)
    exit(2)
}

let args = CommandLine.arguments
guard args.count == 2 else {
    die("usage: catacomb-decode-fixture.swift <copy-of-a-catacomb-component>")
}
let path = args[1]
guard let data = try? Data(contentsOf: URL(fileURLWithPath: path)) else {
    die("cannot read \(path)")
}
guard data.count <= 1 << 20 else {
    die("larger than 1 MiB; refusing to treat this as a component")
}
guard data.prefix(8) == Data("bplist00".utf8) else {
    die("not a binary plist")
}

func sha256(_ data: Data) -> String {
    SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
}

let keys = [
    "CatacombIdentityList",
    "CatacombSecureData",
    "CatacombUserID",
    "CatacombUserUUID",
    "CatacombUserKeybagUUID",
    "CatacombVersion",
]

var out: [String: Any] = [:]
out["bytes"] = data.count
out["sha256"] = sha256(data)

// 0. Envelope only: keys the writer emitted, without instantiating anything.
if let plist = try? PropertyListSerialization.propertyList(from: data, options: [], format: nil),
   let dict = plist as? [String: Any],
   let top = dict["$top"] as? [String: Any] {
    out["archiver"] = dict["$archiver"]
    out["archiveVersion"] = dict["$version"]
    out["topKeys"] = top.keys.sorted()
    out["unknownTopKeys"] = top.keys.filter { !keys.contains($0) }.sorted()
}

// 1. Per-key decode, the way the host reads a component: secure data,
//    user UUIDs, identity list. Non-secure, matching the recovered
//    `decodeObjectOfClass:forKey:` call sites.
do {
    let unarchiver = try NSKeyedUnarchiver(forReadingFrom: data)
    unarchiver.requiresSecureCoding = false

    if let secure = unarchiver.decodeObject(forKey: "CatacombSecureData") as? Data {
        out["secureBytes"] = secure.count
        out["secureSHA256"] = sha256(secure)
        // Header only (magic, version, Apple UID), never the body.
        out["secureHeader"] = secure.prefix(12).map { String(format: "%02x", $0) }.joined()
    } else {
        out["secureBytes"] = "missing"
    }

    if let userID = unarchiver.decodeObject(forKey: "CatacombUserID") as? NSNumber {
        out["catacombUserID"] = userID.intValue
    }
    if let version = unarchiver.decodeObject(forKey: "CatacombVersion") as? NSNumber {
        out["catacombVersion"] = version.intValue
    }
    out["hasUserUUID"] = unarchiver.decodeObject(forKey: "CatacombUserUUID") is NSUUID
    out["hasKeybagUUID"] = unarchiver.decodeObject(forKey: "CatacombUserKeybagUUID") is NSUUID

    if let list = unarchiver.decodeObject(forKey: "CatacombIdentityList") as? [Any] {
        out["identityCount"] = list.count
        out["identityClasses"] = list.map { String(describing: type(of: $0)) }
    } else {
        out["identityCount"] = "missing"
    }
    unarchiver.finishDecoding()
    out["decode"] = "ok"
} catch {
    out["decode"] = "failed"
    out["decodeError"] = String(describing: error)
}

// 2. Secure decode against the recovered class set. If this fails, a
//    loadCatacomb using secure coding would reject the file before SEP
//    ever saw the blob.
var classes: [AnyClass] = [
    NSDictionary.self, NSArray.self, NSMutableArray.self,
    NSData.self, NSMutableData.self, NSDate.self,
    NSUUID.self, NSString.self, NSNumber.self,
]
for name in ["BiometricKitIdentity", "BiometricKitAccessory", "BiometricKitAccessoryGroup"] {
    if let cls = NSClassFromString(name) {
        classes.append(cls)
    } else {
        out["missingClass"] = name
    }
}
do {
    let unarchiver = try NSKeyedUnarchiver(forReadingFrom: data)
    unarchiver.requiresSecureCoding = true
    let list = unarchiver.decodeObject(of: classes, forKey: "CatacombIdentityList")
    let secure = unarchiver.decodeObject(of: [NSData.self], forKey: "CatacombSecureData")
    unarchiver.finishDecoding()
    out["secureDecode"] = (list != nil && secure != nil) ? "ok" : "partial"
} catch {
    out["secureDecode"] = "failed"
    out["secureDecodeError"] = String(describing: error)
}

let json = try JSONSerialization.data(withJSONObject: out, options: [.prettyPrinted, .sortedKeys])
print(String(data: json, encoding: .utf8)!)
