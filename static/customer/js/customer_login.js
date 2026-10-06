document.addEventListener("DOMContentLoaded", () => {
    const phoneInput = document.getElementById("customer-phone");
    const otpInput = document.getElementById("customer-otp");

    const requestOtpBtn = document.getElementById("request-otp-btn");
    const verifyOtpBtn = document.getElementById("verify-otp-btn");
    const backPhoneBtn = document.getElementById("back-phone-btn");

    const phoneStep = document.getElementById("phone-step");
    const otpStep = document.getElementById("otp-step");
    const errorBox = document.getElementById("login-error");

    let challengeId = null;

    function showError(message) {
        errorBox.textContent = message;
        errorBox.classList.remove("d-none");
    }

    function clearError() {
        errorBox.textContent = "";
        errorBox.classList.add("d-none");
    }

    // Request OTP
    requestOtpBtn.addEventListener("click", async () => {
        clearError();

        const phone = phoneInput.value.trim();

        if (!phone) {
            showError("من فضلك أدخل رقم الموبايل.");
            return;
        }

        requestOtpBtn.disabled = true;
        requestOtpBtn.textContent = "جاري إرسال الرمز...";

        try {
            const response = await fetch(
                "/api/v1/auth/login/request-otp/",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        phone: phone,
                    }),
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail ||
                    data.phone?.[0] ||
                    "فشل إرسال رمز التحقق."
                );
            }

            challengeId = data.challenge_id;

            phoneStep.classList.add("d-none");
            otpStep.classList.remove("d-none");

            otpInput.focus();

        } catch (error) {
            console.error(error);
            showError(error.message);
        } finally {
            requestOtpBtn.disabled = false;
            requestOtpBtn.textContent = "إرسال رمز التحقق";
        }
    });

    // Verify OTP
    verifyOtpBtn.addEventListener("click", async () => {
        clearError();

        const otp = otpInput.value.trim();

        if (!challengeId) {
            showError("جلسة التحقق غير صالحة. اطلب رمزًا جديدًا.");
            return;
        }

        if (!otp || otp.length !== 6) {
            showError("من فضلك أدخل رمز التحقق المكون من 6 أرقام.");
            return;
        }

        verifyOtpBtn.disabled = true;
        verifyOtpBtn.textContent = "جاري تسجيل الدخول...";

        try {
            const response = await fetch(
                "/api/v1/auth/login/verify-otp/",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        challenge_id: challengeId,
                        code: otp,
                    }),
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail ||
                    data.code?.[0] ||
                    "رمز التحقق غير صحيح."
                );
            }

            localStorage.setItem(
                "qeta3_customer_access_token",
                data.access
            );

            localStorage.setItem(
                "qeta3_customer_refresh_token",
                data.refresh
            );

            window.location.href = "/";

        } catch (error) {
            console.error(error);
            showError(error.message);

        } finally {
            verifyOtpBtn.disabled = false;
            verifyOtpBtn.textContent = "تأكيد الدخول";
        }
    });

    // Change phone number
    backPhoneBtn.addEventListener("click", () => {
        clearError();

        challengeId = null;
        otpInput.value = "";

        otpStep.classList.add("d-none");
        phoneStep.classList.remove("d-none");

        phoneInput.focus();
    });
});