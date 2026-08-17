"""Static Comms5 connector manifest; no credentials or external registration."""

APPLICATION = "Riverview Comms5"
VERSION = "riverview-comms-contract:5.0"
ENTRYPOINT = "python -m riverview.mcp.comms5_server"
TRANSPORT = "stdio"
TOOLS = {
    "comms5_help", "comms5_capabilities", "comms5_contract_info",
    "comms5_describe_operation", "comms5_examples", "comms5_submit_steward_seed",
    "comms5_store_specification", "comms5_seed_status", "comms5_seed_lineage",
    "comms5_objective_status", "comms5_cme_status", "comms5_recent_steward_submissions",
    "comms5_confirm_and_promote_seed",
}
PROHIBITED = {"direct_sql", "arbitrary_filesystem", "shell", "secret_export", "self_promotion"}
