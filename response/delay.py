"""
Milestone 13: response delay (Phase 5's reply-delay distribution,
made concrete per FR8 from Phase 1 — human-like timing, not instant
replies, and NOT a fixed constant either, since a fixed delay
eventually feels just as robotic as no delay at all).
"""

import random

from shared.logging import get_logger

logger = get_logger(__name__)


def sample_reply_delay() -> float:
    """
    Sample a realistic reply delay in seconds from a log-normal
    distribution — clusters short, with an occasional longer pause,
    rather than every delay being identical or uniformly random.
    """
    # Tuned so most values land roughly in the 2-15 second range,
    # with rare longer outliers - a starting point, not a final tuning
    # (per Phase 6's honest note: decay/timing curves get tuned
    # empirically once the system is actually live).
    delay = random.lognormvariate(mu=1.6, sigma=0.6)
    return round(delay, 2)


if __name__ == "__main__":
    # Proof: sample many delays and confirm real variation, not a
    # fixed constant - exactly the failure mode Phase 5 warned about.
    samples = [sample_reply_delay() for _ in range(20)]
    print("20 sampled delays (seconds):", samples)
    print(f"Min: {min(samples)}, Max: {max(samples)}, Average: {sum(samples)/len(samples):.2f}")
    print("Unique values:", len(set(samples)), "out of 20 (should be close to 20 — i.e. not repeating)")