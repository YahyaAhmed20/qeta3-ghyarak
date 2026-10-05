const QETA3_API = {
    accessTokenKey: "qeta3_access_token",
    refreshTokenKey: "qeta3_refresh_token",

    getAccessToken() {
        return sessionStorage.getItem(this.accessTokenKey);
    },

    getRefreshToken() {
        return sessionStorage.getItem(this.refreshTokenKey);
    },

    setTokens({ access, refresh }) {
        if (access) {
            sessionStorage.setItem(this.accessTokenKey, access);
        }

        if (refresh) {
            sessionStorage.setItem(this.refreshTokenKey, refresh);
        }
    },

    clearTokens() {
        sessionStorage.removeItem(this.accessTokenKey);
        sessionStorage.removeItem(this.refreshTokenKey);
    },

    async refreshAccessToken() {
        const refresh = this.getRefreshToken();

        if (!refresh) {
            return false;
        }

        try {
            const response = await fetch("/api/v1/auth/token/refresh/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    refresh: refresh,
                }),
            });

            if (!response.ok) {
                this.clearTokens();
                return false;
            }

            const data = await response.json();

            if (!data.access) {
                this.clearTokens();
                return false;
            }

            this.setTokens({
    access: data.access,
    refresh: data.refresh || refresh,
});

return true;

        } catch (error) {
            console.error("Token refresh failed:", error);
            this.clearTokens();
            return false;
        }
    },

    async fetch(url, options = {}, retry = true) {
        const headers = {
            ...(options.headers || {}),
        };

        const token = this.getAccessToken();

        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        const response = await fetch(url, {
            ...options,
            headers,
        });

        if (response.status === 401 && retry) {
            const refreshed = await this.refreshAccessToken();

            if (refreshed) {
                return this.fetch(url, options, false);
            }

            this.clearTokens();
            window.location.href = "/seller/login/";
            return response;
        }

        return response;
    },

    async get(url) {
        return this.fetch(url, {
            method: "GET",
        });
    },

    async post(url, data = null) {
        const options = {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
        };

        if (data !== null) {
            options.body = JSON.stringify(data);
        }

        return this.fetch(url, options);
    },

    async patch(url, data = {}) {
        return this.fetch(url, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
        });
    },

    async delete(url) {
        return this.fetch(url, {
            method: "DELETE",
        });
    },
};

document.addEventListener("DOMContentLoaded", () => {
    const logoutButton = document.getElementById("logout-button");

    if (!logoutButton) {
        return;
    }

    logoutButton.addEventListener("click", () => {
        QETA3_API.clearTokens();

        window.location.href = "/seller/login/";
    });
});