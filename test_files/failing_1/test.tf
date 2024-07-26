
resource "google_project_iam_binding" "google_deployment_accounts_compute_admin" {
  project = "fxci-production-level3-workers"
  role    = "roles/compute.admin"
  member  = "serviceAccount:${module.google_deployment_accounts.service_account.email}"
}
