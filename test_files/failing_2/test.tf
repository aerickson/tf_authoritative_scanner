resource "google_project_iam_binding" "google_deployment_accounts_compute_admin" {
  project = "fxci-production-level3-workers"
  role    = "roles/compute.admin"
  member  = "serviceAccount:test3333"
}



resource "google_project_iam_binding" "google_deployment_accounts_compute_admin3" {
  project = "fxci-production-level3-workers"
  role    = "roles/compute.admin"
  member  = "serviceAccount:test111"
}



resource "google_project_iam_binding" "google_deployment_accounts_compute_admin4" {
  project = "fxci-production-level3-workers"
  role    = "roles/compute.admin"
  member  = "serviceAccount:4444"
}
