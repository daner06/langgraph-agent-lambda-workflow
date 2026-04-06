variable "prefix" {
  description = "Resource name prefix (keep it consistent with the backend prefix)."
  type        = string
  default     = "cd"
}

variable "environment" {
  description = "Environment tag."
  type        = string
  default     = "dev"
}
