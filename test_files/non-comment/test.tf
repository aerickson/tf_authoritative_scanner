# terraform_authoritative_scanner_ok
resource "non_authoritative" "google_deployment_accounts_compute_admin_google_project_iam_binding" {
  project = "fxci-production-level3-workers"
  role    = "roles/compute.admin"
  member  = "serviceAccount:test3333"
}
