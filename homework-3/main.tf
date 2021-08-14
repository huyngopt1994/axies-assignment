terraform {
  required_providers {
    github = {
      source  = "integrations/github"
      version = "4.13.0"
    }
  }
}

provider "github" {
  # Configuration options
}

locals {
  flatten_mappings = flatten([
    for team_name, team_mapping in local.team_mappings : [
      for role, users in team_mapping : [
        for user in users : {
          team_name = team_name
          role      = role
          user      = user
        }
      ]
    ]
  ])
}

resource "github_team" "team" {
  for_each = local.team_mappings
  name     = each.key
}

resource "github_team_membership" "team_membership" {
  for_each = {
    for mapping in local.flatten_mappings : github_team.team[mapping.team_name].id => mapping
  }
  team_id  = each.key
  username = each.value.user
  role     = each.value.role
}
