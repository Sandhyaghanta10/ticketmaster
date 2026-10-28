import pytest

from ticketmaster.otp import OtpError, OtpService


class Clock:
    now = 0.0

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def otp(clock):
    return OtpService(clock=clock, ttl_s=300, max_attempts=3, code_factory=lambda: "123456")


MOBILE = "9876543210"


def test_happy_path_and_code_is_single_use(otp):
    assert otp.issue("Asha Rani", MOBILE) == "123456"
    otp.verify(MOBILE, "123456")
    with pytest.raises(OtpError, match="Request an OTP"):
        otp.verify(MOBILE, "123456")  # already consumed


@pytest.mark.parametrize("name,mobile,msg", [
    ("", MOBILE, "letters"),
    ("Asha1", MOBILE, "letters"),
    ("Asha", "12345", "10-digit"),
    ("Asha", "5876543210", "10-digit"),   # must start with 6-9
    ("Asha", "98765432100", "10-digit"),
    ("Asha", "98765abcde", "10-digit"),
])
def test_input_validation(otp, name, mobile, msg):
    with pytest.raises(OtpError, match=msg):
        otp.issue(name, mobile)


def test_verify_without_issue(otp):
    with pytest.raises(OtpError, match="Request an OTP"):
        otp.verify(MOBILE, "123456")


def test_wrong_code_counts_down_then_locks_out(otp):
    otp.issue("Asha", MOBILE)
    with pytest.raises(OtpError, match="2 attempts left"):
        otp.verify(MOBILE, "000000")
    with pytest.raises(OtpError, match="1 attempts left"):
        otp.verify(MOBILE, "000001")
    with pytest.raises(OtpError, match="Too many"):
        otp.verify(MOBILE, "000002")
    with pytest.raises(OtpError, match="Request an OTP"):
        otp.verify(MOBILE, "123456")  # even the right code is dead after lockout


def test_code_expires(otp, clock):
    otp.issue("Asha", MOBILE)
    clock.now = 299
    otp.verify(MOBILE, "123456")  # still fine just before the deadline
    otp.issue("Asha", MOBILE)
    clock.now = 299 + 300
    with pytest.raises(OtpError, match="expired"):
        otp.verify(MOBILE, "123456")


def test_new_otp_replaces_old_one(otp):
    otp.issue("Asha", MOBILE)
    codes = iter(["654321"])
    otp._code_factory = lambda: next(codes)
    otp.issue("Asha", MOBILE)
    with pytest.raises(OtpError):
        otp.verify(MOBILE, "123456")


def test_default_codes_are_six_digits_and_vary():
    service = OtpService()
    codes = {service.issue("Asha", MOBILE) for _ in range(20)}
    assert all(len(c) == 6 and c.isdigit() for c in codes) and len(codes) > 1
