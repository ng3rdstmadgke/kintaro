class AlertComponent {
  static info(message) {
    AlertComponent.alert("info", message)
  }
  static success(message) {
    AlertComponent.alert("success", message)
  }
  static warning(message) {
    AlertComponent.alert("warning", message)
  }
  static error(message) {
    AlertComponent.alert("error", message)
  }
  static alert(type, message) {
    let alertClass = ""
    let alertIcon = ""
    if (type === "success") {
      alertIcon = "bi-check-circle-fill"
      alertClass = "alert-success"
    } else if (type === "info") {
      alertIcon = "bi-info-fill"
      alertClass = "alert-primary"
    } else if (type === "warning") {
      alertIcon = "bi-exclamation-triangle-fill"
      alertClass = "alert-warning"
    } else if (type === "error") {
      alertIcon = "bi-exclamation-triangle-fill"
      alertClass = "alert-danger"
    }

    let html = `
      <div class="alert ${alertClass} alert-dismissible fade show d-flex align-items-center" role="alert">
        <div class="flex-shrink-0 me-2">
          <i class="bi ${alertIcon}" style="font-size: 20px;"></i>
        </div>
        <div>
          ${CommonUtil.escape_html(message)}
        </div>
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
      </div>
    `
    document.getElementById("js_kintaro_alert").insertAdjacentHTML("beforeend", html)
  }
}