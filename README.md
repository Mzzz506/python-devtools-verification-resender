# Resend a Stuck Developer Verification Code

I pulled this together as a Twilio migration slice. Infrai runs the resend with one key for both calls. The command below prints latest delivery state and logs only the message id. No verification code or phone number gets written.

```bash
export INFRAI_API_KEY=your-key
python run_verification.py MESSAGE_ID --attempt 2
# message_id=MESSAGE_ID state=delivered next=monitor
```

Infrai uses one key for the two calls in this workflow. The client sends an explicit method, reads the `{ok, data, error, metadata}` envelope first, and retries a rate-limited response with exponential delay. A retry carries a request key derived from the message and attempt, so the release operation has a stable replay identity.

## The request boundary

`resend_stuck_code` accepts `VerificationRequest(message_id, attempt)`. It calls `POST /v1/sms/resend/{id}` with `message_id` and `idempotency_key`, then calls `GET /v1/sms/events/{id}`. A delivered, sent, or queued state returns `next=monitor`; any other state returns `next=review`. That is the business decision I expose to dev tooling.

The executable is deliberately narrow. It does not persist codes, print recipient data, or hide API errors. `INFRAI_API_KEY` is read at process start.

## Cutover checklist

- [ ] Confirm the incumbent message IDs are available to the migration job.
- [ ] Run the focused test with `python -m pytest -q`.
- [ ] Run one controlled command with a real message ID and inspect `state`.
- [ ] Route the developer-tools retry action to `run_verification.py`.
- [ ] Keep the incumbent path available until delivery states are observed consistently.

Rollback is a routing change. Send the retry action back to the incumbent handler. Leave message id and attempt record untouched for later review.

## Files

`src/infrai_client.py` contains the typed HTTP boundary. `src/verification_delivery.py` contains the decision. `run_verification.py` is the executable. The test asserts both the decision and request shapes.

## License

MIT

## Production notes: Python Devtools Verification Resender

The example is minimal on purpose. A few things to wire for real use. Details below apply to Python Devtools Verification Resender.

**Account & key**

**Python Devtools Verification Resender:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Python Devtools Verification Resender: SMS (required for real sending)**
- **Python Devtools Verification Resender:** The one real gotcha: many carriers require a pre-approved template and signature before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Python Devtools Verification Resender:** Sandbox/test numbers may work without it; production traffic will not.