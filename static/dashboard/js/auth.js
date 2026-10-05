document.addEventListener("DOMContentLoaded", () => {
    const requestOtpButton =
        document.getElementById("request-otp-btn");

    const verifyOtpButton =
        document.getElementById("verify-otp-btn");

    const backButton =
        document.getElementById("back-to-phone-btn");

    if (requestOtpButton) {
        requestOtpButton.addEventListener(
            "click",
            requestLoginOTP
        );
    }

    if (verifyOtpButton) {
        verifyOtpButton.addEventListener(
            "click",
            verifyLoginOTP
        );
    }

    if (backButton) {
        backButton.addEventListener(
            "click",
            backToPhone
        );
    }
});


async function requestLoginOTP() {
    const phoneInput = document.getElementById("phone");
    const button = document.getElementById("request-otp-btn");

    const phone = phoneInput.value.trim();

    if (!phone) {
        showAuthMessage(
            "من فضلك أدخل رقم الهاتف.",
            "error"
        );
        return;
    }

    setButtonLoading(
        button,
        true,
        "جاري إرسال رمز التحقق..."
    );

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
                getApiErrorMessage(data)
            );
        }

        /*
         * Save challenge ID temporarily.
         * It will be used in the OTP verification step.
         */
        sessionStorage.setItem(
            "qeta3_login_challenge_id",
            data.challenge_id
        );

        document
            .getElementById("phone-step")
            .classList.add("d-none");

        document
            .getElementById("otp-step")
            .classList.remove("d-none");

        showAuthMessage(
            "تم إرسال رمز التحقق إلى رقم الهاتف.",
            "success"
        );

    } catch (error) {

        console.error(
            "Request OTP error:",
            error
        );

        showAuthMessage(
            error.message ||
            "حدث خطأ أثناء إرسال رمز التحقق.",
            "error"
        );

    } finally {

        setButtonLoading(
            button,
            false,
            "إرسال رمز التحقق"
        );
    }
}


async function verifyLoginOTP() {
    const otpInput =
        document.getElementById("otp");

    const button =
        document.getElementById("verify-otp-btn");

    const challengeId =
        sessionStorage.getItem(
            "qeta3_login_challenge_id"
        );

    const code =
        otpInput.value.trim();

    if (!challengeId) {
        showAuthMessage(
            "جلسة التحقق انتهت. اطلب رمزًا جديدًا.",
            "error"
        );
        return;
    }

    if (!/^\d{6}$/.test(code)) {
        showAuthMessage(
            "أدخل رمز التحقق المكون من 6 أرقام.",
            "error"
        );
        return;
    }

    setButtonLoading(
        button,
        true,
        "جاري تسجيل الدخول..."
    );

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
                    code: code,
                }),
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                getApiErrorMessage(data)
            );
        }

        if (!data.access || !data.refresh) {
            throw new Error(
                "لم يتم استلام رموز تسجيل الدخول."
            );
        }

        sessionStorage.setItem(
            "qeta3_access_token",
            data.access
        );

        sessionStorage.setItem(
            "qeta3_refresh_token",
            data.refresh
        );

        sessionStorage.removeItem(
            "qeta3_login_challenge_id"
        );

        showAuthMessage(
            "تم تسجيل الدخول بنجاح. جاري فتح لوحة التحكم...",
            "success"
        );

        window.location.href =
            "/dashboard/";

    } catch (error) {

        console.error(
            "Verify OTP error:",
            error
        );

        showAuthMessage(
            error.message ||
            "حدث خطأ أثناء تسجيل الدخول.",
            "error"
        );

    } finally {

        setButtonLoading(
            button,
            false,
            "تسجيل الدخول"
        );
    }
}


function backToPhone() {
    document
        .getElementById("otp-step")
        .classList.add("d-none");

    document
        .getElementById("phone-step")
        .classList.remove("d-none");

    document
        .getElementById("otp")
        .value = "";

    sessionStorage.removeItem(
        "qeta3_login_challenge_id"
    );

    const message =
        document.getElementById("auth-message");

    if (message) {
        message.classList.add("d-none");
    }
}


function showAuthMessage(message, type) {
    const element =
        document.getElementById("auth-message");

    if (!element) {
        return;
    }

    element.textContent = message;

    element.classList.remove(
        "d-none",
        "success",
        "error"
    );

    element.classList.add(type);
}


function setButtonLoading(
    button,
    loading,
    loadingText
) {
    if (!button) {
        return;
    }

    if (loading) {
        button.disabled = true;

        button.dataset.originalText =
            button.textContent;

        button.textContent = loadingText;

    } else {
        button.disabled = false;

        button.textContent =
            button.dataset.originalText ||
            loadingText;
    }
}


function getApiErrorMessage(data) {

    if (!data) {
        return "حدث خطأ غير متوقع.";
    }

    if (typeof data.detail === "string") {
        return data.detail;
    }

    if (typeof data.phone === "string") {
        return data.phone;
    }

    const firstError =
        Object.values(data)[0];

    if (Array.isArray(firstError)) {
        return firstError[0];
    }

    if (typeof firstError === "string") {
        return firstError;
    }

    return "حدث خطأ أثناء تنفيذ الطلب.";
}