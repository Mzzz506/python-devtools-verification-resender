import argparse

from src.infrai_client import InfraiClient
from src.verification_delivery import VerificationRequest, resend_stuck_code


def main() -> None:
    parser = argparse.ArgumentParser(description="Resend a developer verification code and print delivery state.")
    parser.add_argument("message_id")
    parser.add_argument("--attempt", type=int, default=1)
    args = parser.parse_args()
    report = resend_stuck_code(VerificationRequest(args.message_id, args.attempt), InfraiClient())
    print(f"message_id={report.message_id} state={report.state} next={report.action}")


if __name__ == "__main__":
    main()
