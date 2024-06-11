class CookieUtil {
  static get(key) {
    let obj = Object.fromEntries(
      document.cookie
        .split(";")
        .map((e) => {
          return e.trim()
            .split("=")
            .map((k) => {
              return decodeURIComponent(k);
            });
        })
    );
    return obj[key];
  }
  
  static set(key, value) {
    document.cookie = `${encodeURIComponent(key)}=${encodeURIComponent(value)}`;
  }

  static delete(key) {
    document.cookie = `${encodeURIComponent(key)}=; max-age=0`;
  }
}

class AuthUtil {
  static TOKEN_KEY = "token"

  static authenticated() {
    let payload = AuthUtil.getPayload()
    if (payload) {
      // トークンの有効期限を検証
      let now  = Math.floor((new Date()).getTime() / 1000)
      return payload.exp > now
    }
    return false
  }

  static isAuthenticated() {
    return localStorage.getItem('token') !== null;
  }

  // CookieからJWTを削除
  static logout() {
    CookieUtil.delete(AuthUtil.TOKEN_KEY);
  }

  // JWTをCookieに保存
  static login(token) {
    CookieUtil.set(AuthUtil.TOKEN_KEY, token);
  }

  static getToken() {
    return CookieUtil.get(AuthUtil.TOKEN_KEY)
  }

  static getPayload() {
    let token = CookieUtil.get(AuthUtil.TOKEN_KEY)
    if (!token) return null
    let payload = token.split(".")[1]
    let decoded = atob(payload)
    return JSON.parse(decoded)
  }
}

class FetchUtil {
  static async fetch(url, options = {}) {
    if (!options.headers) {
      options.headers = {}
    }
    if (AuthUtil.authenticated()) {
      options.headers["Authorization"] = `Bearer ${AuthUtil.getToken()}`
    }
    let response = await fetch(url, options)
    let json = await response.json()
    if (!response.ok) {
      throw new Error(json.message || response.statusText)
    }
    return json
  }

  static async get(url) {
    return await FetchUtil.fetch(url)
  }

  static async post(url, data, headers = {}) {
    headers["Content-Type"] = "application/json"
    return await FetchUtil.fetch(url, {
      method: "POST",
      headers: headers,
      body: JSON.stringify(data)
    })
  }

  static async put(url, data, headers = {}) {
    headers["Content-Type"] = "application/json"
    return await FetchUtil.fetch(url, {
      method: "PUT",
      headers: headers,
      body: JSON.stringify(data)
    })
  }

  static async delete(url) {
    return await FetchUtil.fetch(url, {
      method: "DELETE",
      headers: {},
    })
  }
}