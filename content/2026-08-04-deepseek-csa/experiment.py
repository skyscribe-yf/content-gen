#!/usr/bin/env python3
"""Transparent attention-count experiment for the DeepSeek-V4 article.

This is a mechanism demonstration, not a model benchmark. It counts visible
query-key pairs under causal masking for dense attention, V3.2-style DSA, CSA,
and HCA. The community mini implementation is validated separately with its
own unit tests.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Counts:
    length: int
    dense_pairs: int
    dsa_indexer_pairs: int
    dsa_core_pairs: int
    csa_indexer_pairs: int
    csa_core_pairs: int
    csa_local_pairs: int
    hca_global_pairs: int
    hca_local_pairs: int
    dense_entries: int
    csa_entries: int
    hca_entries: int


def visible_window(token: int, width: int) -> int:
    return min(token + 1, width)


def count_attention(
    length: int,
    compression_factor: int,
    hca_factor: int,
    top_k: int,
    window: int,
) -> Counts:
    if min(length, compression_factor, hca_factor, top_k, window) <= 0:
        raise ValueError("all parameters must be positive")

    dense_pairs = sum(token + 1 for token in range(length))
    dsa_indexer_pairs = dense_pairs
    dsa_core_pairs = sum(min(token + 1, top_k) for token in range(length))

    csa_indexer_pairs = 0
    csa_core_pairs = 0
    csa_local_pairs = 0
    hca_global_pairs = 0
    hca_local_pairs = 0

    for token in range(length):
        # The current compressed block is still incomplete. The exact local
        # window carries its information until the block is flushed.
        csa_blocks = token // compression_factor
        hca_blocks = token // hca_factor
        csa_indexer_pairs += csa_blocks
        csa_core_pairs += min(csa_blocks, top_k)
        csa_local_pairs += visible_window(token, window)
        hca_global_pairs += hca_blocks
        hca_local_pairs += visible_window(token, window)

    return Counts(
        length=length,
        dense_pairs=dense_pairs,
        dsa_indexer_pairs=dsa_indexer_pairs,
        dsa_core_pairs=dsa_core_pairs,
        csa_indexer_pairs=csa_indexer_pairs,
        csa_core_pairs=csa_core_pairs,
        csa_local_pairs=csa_local_pairs,
        hca_global_pairs=hca_global_pairs,
        hca_local_pairs=hca_local_pairs,
        dense_entries=length,
        csa_entries=math.ceil(length / compression_factor),
        hca_entries=math.ceil(length / hca_factor),
    )


def parse_lengths(value: str) -> list[int]:
    lengths = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not lengths or any(length <= 0 for length in lengths):
        raise ValueError("lengths must be a comma-separated list of positive integers")
    return lengths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lengths", default="512,1024,2048,4096")
    parser.add_argument("--compression-factor", type=int, default=8)
    parser.add_argument("--hca-factor", type=int, default=32)
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--window", type=int, default=16)
    args = parser.parse_args()

    print(
        "# mechanism-counts "
        f"m={args.compression_factor} "
        f"m_prime={args.hca_factor} "
        f"k={args.top_k} "
        f"window={args.window}"
    )
    print(
        "length,dense_pairs,dsa_indexer_pairs,dsa_core_pairs,"
        "csa_indexer_pairs,csa_core_pairs,csa_local_pairs,"
        "hca_global_pairs,hca_local_pairs,dense_entries,csa_entries,hca_entries"
    )

    for length in parse_lengths(args.lengths):
        counts = count_attention(
            length=length,
            compression_factor=args.compression_factor,
            hca_factor=args.hca_factor,
            top_k=args.top_k,
            window=args.window,
        )
        print(",".join(str(value) for value in counts.__dict__.values()))


if __name__ == "__main__":
    main()
