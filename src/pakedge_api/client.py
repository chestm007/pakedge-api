"""Pakedge API client for managed switches (SX-24P16, etc.)."""

from __future__ import annotations

import logging
from typing import Any

import requests

from pakedge_api.parser import parse_pipe_array, parse_quoted_object, parse_response
from pakedge_api.models import (
    PortStatus,
    FirmwareInfo,
    SystemInfo,
    SystemTime,
    SystemUser,
    SystemStatus,
    IPConfig,
    VLANSetting,
    STPGlobal,
    LLDPNeighbor,
    PoEGlobal,
    QoSSchedule,
    SNMPAgent,
    PortConfig,
    PortStatistics,
    MirrorConfig,
    TrunkAggr,
    TrunkLACP,
    MACAddress,
    MACStatic,
    PortFlowControl,
    PortStormControl,
    PortRateLimit,
    PoEPort,
    Dot1XPort,
    VLANAccessPort,
    VLANTrunkPort,
    VLANHybridPort,
    VLANMAC,
    VLANProtocol,
    VLANProtoVLAN,
    OUIEntry,
    VoicePort,
    VoiceVLAN,
    QoS8021p,
    QoSDSCP,
    QoSPortPriority,
    ACLRule,
    STPInstance,
    STPPortConfig,
    STPMSTIPortConfig,
    STPStatistics,
    IGMPGlobal,
    IGMPVLAN,
    IGMPGroup,
    IGMPFastLeave,
    IGMPMulticastFilter,
    DHCPRelay,
    DHCPService,
    DHCPSnoopingGlobal,
    DHCPSnoopingPort,
    DHCPSnoopingUser,
    ARPDefense,
    WormDefense,
    DOSDefense,
    MACDefense,
    PortFilter,
    MACFilter,
    Dot1XGlobal,
    Dot1XFrame,
    SNMPGroup,
    SNMPUser,
    SNMPView,
    SNMPTrap,
    LLDPGlobal,
    LLDPPort,
    LLDPStatistic,
    SyslogServer,
    SyslogLogConfig,
    SSLConfig,
    SysTimeRange,
    TimerangeEntry,
    SecFilter,
    SecImpb,
    SecOneKeyBind,
)

logger = logging.getLogger(__name__)


class PakedgeError(Exception):
    """Base exception for Pakedge API errors."""


class PakedgeAuthError(PakedgeError):
    """Authentication failed."""


class PakedgeSessionExpired(PakedgeError):
    """Session has timed out."""


class PakedgeClient:
    """Client for Pakedge managed switches.

    Uses the same CGI-based interface as the web UI. All endpoints
    use GET requests with query parameters. Session state is managed
    via cookies.
    """

    def __init__(
        self,
        host: str,
        username: str = "pakedge",
        password: str = "",
        timeout: float = 10.0,
    ) -> None:
        self.host = host
        self.username = username
        self.password = password
        self.timeout = timeout
        self._session = requests.Session()
        self._logged_in = False

    @property
    def logged_in(self) -> bool:
        return self._logged_in

    def login(self) -> None:
        """Authenticate with the switch.

        The PakEdge uses a client-side cookie (``usa_Pakedge_user``)
        for session management — there is no server-side session.
        The cookie format is ``username|0``.
        """
        url = f"http://{self.host}/cgi/login_pkd"
        params = {"username": self.username, "password": self.password}

        try:
            resp = self._session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise PakedgeError(f"Login failed: {exc}") from exc

        # The PakEdge sets the session cookie client-side (JS).
        # We replicate the JS behavior: document.cookie = "usa_Pakedge_user=" + username + "|0"
        self._session.cookies.set(
            "usa_Pakedge_user",
            f"{self.username}|0",
            domain=self.host,
            path="/",
        )
        self._logged_in = True
        logger.info("Logged in to %s as %s", self.host, self.username)

    def logout(self) -> None:
        """Invalidate the session."""
        if not self._logged_in:
            return

        try:
            self._session.get(
                f"http://{self.host}/cgi/logout_pkd",
                timeout=self.timeout,
            )
        except requests.RequestException:
            pass  # Best effort

        self._logged_in = False
        self._session.cookies.clear()

    def _request(self, endpoint: str, params: dict[str, str] | None = None) -> str:
        """Make a GET request to a CGI endpoint.

        Raises:
            PakedgeSessionExpired: If the session has timed out.
        """
        if not self._logged_in:
            raise PakedgeError("Not logged in. Call login() first.")

        url = f"http://{self.host}/{endpoint}"
        params = {**(params or {}), "rand": str(id(self))}

        try:
            resp = self._session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise PakedgeError(f"Request to {endpoint} failed: {exc}") from exc

        # Check for session timeout (the JS checks for return value 20)
        if resp.text.strip() == "20":
            self._logged_in = False
            raise PakedgeSessionExpired("Session expired")

        return resp.text

    def _get_raw(self, endpoint: str, params: dict[str, str] | None = None) -> str:
        """Get raw response string from an endpoint."""
        return self._request(endpoint, params)

    def _get_parsed(self, endpoint: str, params: dict[str, str] | None = None) -> dict[str, Any] | list[dict[str, Any]]:
        """Get and parse response from an endpoint."""
        raw = self._request(endpoint, params)
        return parse_response(raw)

    # ─── System Endpoints ───────────────────────────────────────────────

    def get_system_info(self) -> SystemInfo:
        """Get system information (name, description, version, uptime, etc.)."""
        data = self._get_parsed("cgi/get_sysInfo_pkd")
        if isinstance(data, dict):
            return SystemInfo(
                description=data.get("system_desc", ""),
                version=data.get("system_version", ""),
                product_intf=data.get("product_intf", 0),
                uptime=data.get("system_uptime", 0),
                name=data.get("system_name", ""),
                location=data.get("system_location", ""),
                management_vlan=data.get("management_vlan", 0),
                mac_age=data.get("mac_age", 0),
                login_timeout=data.get("login_timeout", 0),
                dhcp_enabled=bool(data.get("dhcp_enabled", 0)),
                ip_address=data.get("ip_address", ""),
                gateway=data.get("gateway", ""),
                dns=data.get("dns", ""),
            )
        return SystemInfo()

    def get_system_time(self) -> SystemTime:
        """Get system time configuration."""
        data = self._get_parsed("cgi/get_sysTime_pkd")
        if isinstance(data, dict):
            return SystemTime(
                current_time=data.get("cur_time", ""),
                timezone=data.get("time_zone_offset", ""),
                sntp_state=data.get("sntp_state", 0),
                primary_server=data.get("pri_server_ip", ""),
                secondary_server=data.get("senc_server_ip", ""),
                poll_time=data.get("poll_time", 0),
            )
        return SystemTime()

    def get_system_user(self) -> SystemUser:
        """Get current user account info."""
        data = self._get_parsed("cgi/get_sysUser_pkd")
        if isinstance(data, dict):
            return SystemUser(
                username=data.get("username", ""),
                privilege=data.get("privilege", 0),
            )
        return SystemUser()

    def get_system_status(self) -> SystemStatus:
        """Get system resource status (CPU, memory, temperature)."""
        data = self._get_parsed("cgi/get_sys_source_pkd")
        if isinstance(data, dict):
            return SystemStatus(
                cpu_usage=data.get("cpu_usage", ""),
                memory_usage=data.get("mem_usage", ""),
                temperature=data.get("tempre", ""),
            )
        return SystemStatus()

    def get_ip_config(self) -> IPConfig:
        """Get IP configuration."""
        data = self._get_parsed("cgi/get_sysIp_pkd")
        if isinstance(data, dict):
            return IPConfig(
                ip_address=data.get("ip_address", ""),
                subnet_mask=data.get("subnet_mask", ""),
                gateway=data.get("gateway", ""),
                dns=data.get("dns", ""),
            )
        return IPConfig()

    def get_vlan_setting(self) -> VLANSetting:
        """Get VLAN settings."""
        data = self._get_parsed("cgi/get_vlan_setting_pkd")
        if isinstance(data, dict):
            return VLANSetting(
                vlan_type=data.get("vlanType", 1),
            )
        return VLANSetting()

    def get_system_ssl(self) -> SSLConfig:
        """Get SSL/TLS configuration."""
        data = self._get_parsed("cgi/get_sys_ssl_pkd")
        if isinstance(data, dict):
            return SSLConfig(
                enabled=bool(data.get("enabled", 0)),
                cert_subject=data.get("cert_subject", ""),
                cert_expiry=data.get("cert_expiry", ""),
            )
        return SSLConfig()

    # ─── Port Endpoints ─────────────────────────────────────────────────

    def get_port_status(self) -> list[PortStatus]:
        """Get the status of all switch ports.

        Returns a list of PortStatus objects, one per port (1-indexed).
        Port data is returned as pipe-delimited JSON objects.
        """
        raw = self._request("cgi/port_basicInfo_pkd")
        data_list = parse_pipe_array(raw)
        return [
            PortStatus(
                port=item.get("port", i + 1),
                state=item.get("state", 0),
                linkstatus=item.get("linkstatus", 0),
                pvid=item.get("pvid", 1),
            )
            for i, item in enumerate(data_list)
        ]

    def get_port_config(self) -> list[PortConfig]:
        """Get port configuration for all ports."""
        raw = self._request("cgi/get_portCommon_pkd")
        data_list = parse_pipe_array(raw)
        return [
            PortConfig(
                port=item.get("port", i + 1),
                linkstatus=item.get("linkstatus", 0),
                state=item.get("state", 0),
                autocfg=item.get("autocfg", 0),
                port_type=item.get("port_type", 0),
                pvid=item.get("pvid", 1),
                jumbo=item.get("jumbo", 9216),
            )
            for i, item in enumerate(data_list)
        ]

    def get_port_statistics(self) -> list[PortStatistics]:
        """Get port statistics counters for all ports."""
        raw = self._request("cgi/get_port_statistics_pkd")
        data_list = parse_pipe_array(raw)
        return [
            PortStatistics(
                port=item.get("port", i + 1),
                rx_octets=item.get("RxOctets", 0),
                rx_unicast_pkts=item.get("RxUnicastPkts", 0),
                rx_nonunicast_pkts=item.get("RxNonUnicastPkts", 0),
                rx_errors=item.get("RxErrorsPackets", 0),
                rx_discard=item.get("RxDiscardPackets", 0),
                tx_octets=item.get("TxOctets", 0),
                tx_unicast_pkts=item.get("TxUnicastPkts", 0),
                tx_nonunicast_pkts=item.get("TxNonUnicastPkts", 0),
                tx_errors=item.get("TxErrorsPackets", 0),
                tx_discard=item.get("TxDiscardPackets", 0),
            )
            for i, item in enumerate(data_list)
        ]

    def get_port_flow_control(self) -> list[PortFlowControl]:
        """Get port flow control configuration."""
        raw = self._request("cgi/get_portFlowCtrl_pkd")
        data_list = parse_pipe_array(raw)
        return [
            PortFlowControl(
                port=item.get("port", i + 1),
                rx_enabled=bool(item.get("rx_enabled", 0)),
                tx_enabled=bool(item.get("tx_enabled", 0)),
            )
            for i, item in enumerate(data_list)
        ]

    def get_port_storm_control(self) -> list[PortStormControl]:
        """Get broadcast/multicast/unicast storm control."""
        raw = self._request("cgi/get_portBcStorm_pkd")
        data_list = parse_pipe_array(raw)
        return [
            PortStormControl(
                port=item.get("port", i + 1),
                bc_rate=item.get("bc_rate", 0),
                mc_rate=item.get("mc_rate", 0),
                uc_rate=item.get("uc_rate", 0),
            )
            for i, item in enumerate(data_list)
        ]

    def get_port_rate_limit(self) -> list[PortRateLimit]:
        """Get port rate limiting configuration."""
        raw = self._request("cgi/get_portRatelimit_pkd")
        data_list = parse_pipe_array(raw)
        return [
            PortRateLimit(
                port=item.get("port", i + 1),
                rx_rate=item.get("rx_rate", 0),
                tx_rate=item.get("tx_rate", 0),
            )
            for i, item in enumerate(data_list)
        ]

    def get_mirror_config(self) -> list[MirrorConfig]:
        """Get port mirroring configuration."""
        raw = self._request("cgi/get_mirror_pkd")
        data_list = parse_pipe_array(raw)
        return [
            MirrorConfig(
                mirror_type=item.get("mirror_type", 0),
                source_port=item.get("source_port", ""),
                destination_port=item.get("destination_port", ""),
            )
            for i, item in enumerate(data_list)
        ]

    def get_trunk_aggregation(self) -> list[TrunkAggr]:
        """Get static link aggregation configuration."""
        raw = self._request("cgi/get_trunk_aggr_pkd")
        data_list = parse_pipe_array(raw)
        return [
            TrunkAggr(
                group_id=item.get("group_id", 0),
                ports=item.get("ports", ""),
                mode=item.get("mode", 0),
            )
            for i, item in enumerate(data_list)
        ]

    def get_trunk_lacp(self) -> list[TrunkLACP]:
        """Get LACP aggregation configuration."""
        raw = self._request("cgi/get_trunk_lacp_pkd")
        data_list = parse_pipe_array(raw)
        return [
            TrunkLACP(
                group_id=item.get("group_id", 0),
                ports=item.get("ports", ""),
                system_priority=item.get("system_priority", 0),
                port_priority=item.get("port_priority", 0),
                key=item.get("key", 0),
            )
            for i, item in enumerate(data_list)
        ]

    def get_poe_global(self) -> PoEGlobal:
        """Get PoE global configuration."""
        data = self._get_parsed("cgi/get_poe_global_pkd")
        if isinstance(data, dict):
            return PoEGlobal(
                power_mgmt_mode=data.get("power_mgntmode", 0),
                usage_ratio=data.get("use_ratio", ""),
                chip_temp=data.get("poechip_tempre", ""),
            )
        return PoEGlobal()

    def get_poe_port(self) -> list[PoEPort]:
        """Get per-port PoE configuration."""
        raw = self._request("cgi/get_poe_port_pkd")
        data_list = parse_pipe_array(raw)
        return [
            PoEPort(
                port=item.get("port", i + 1),
                enabled=bool(item.get("enabled", 0)),
                priority=item.get("priority", 0),
                max_power=item.get("max_power", 0),
                actual_power=item.get("actual_power", 0),
                status=item.get("status", ""),
            )
            for i, item in enumerate(data_list)
        ]

    def get_dot1x_port(self) -> list[Dot1XPort]:
        """Get 802.1X port configuration."""
        raw = self._request("cgi/get_dot1x_port_pkd")
        data_list = parse_pipe_array(raw)
        return [
            Dot1XPort(
                port=item.get("port", i + 1),
                enabled=bool(item.get("enabled", 0)),
                mode=item.get("mode", ""),
            )
            for i, item in enumerate(data_list)
        ]

    def get_mac_list(self) -> list[MACAddress]:
        """Get MAC address table."""
        raw = self._request("cgi/get_mac_maclist_pkd")
        data_list = parse_pipe_array(raw)
        return [
            MACAddress(
                port=item.get("port", ""),
                mac=item.get("mac", ""),
                vlan=item.get("vlan", 0),
                type=item.get("type", ""),
            )
            for i, item in enumerate(data_list)
        ]

    def get_mac_static(self) -> list[MACStatic]:
        """Get static MAC address entries."""
        raw = self._request("cgi/get_mac_staticmac_pkd")
        data_list = parse_pipe_array(raw)
        return [
            MACStatic(
                mac=item.get("mac", ""),
                port=item.get("port", ""),
                vlan=item.get("vlan", 0),
            )
            for i, item in enumerate(data_list)
        ]

    # ─── VLAN Endpoints ─────────────────────────────────────────────────

    def get_vlan_access_port(self) -> list[VLANAccessPort]:
        """Get access port VLAN configuration."""
        raw = self._request("cgi/get_vlan_accessport_pkd")
        data_list = parse_pipe_array(raw)
        return [
            VLANAccessPort(
                port=item.get("port", i + 1),
                pvid=item.get("pvid", 1),
                member_type=item.get("member_type", "untagged"),
            )
            for i, item in enumerate(data_list)
        ]

    def get_vlan_mac(self) -> list[VLANMAC]:
        """Get MAC-based VLAN entries."""
        raw = self._request("cgi/get_vlan_macvlan_pkd")
        data_list = parse_pipe_array(raw)
        return [
            VLANMAC(
                vlan_id=item.get("vlan_id", 0),
                mac=item.get("mac", ""),
                priority=item.get("priority", 0),
            )
            for i, item in enumerate(data_list)
        ]

    def get_vlan_protocol(self) -> list[VLANProtocol]:
        """Get protocol-based VLAN entries."""
        raw = self._request("cgi/get_vlan_proto_pkd")
        data_list = parse_pipe_array(raw)
        return [
            VLANProtocol(
                vlan_id=item.get("vlan_id", 0),
                protocol=item.get("protocol", ""),
                priority=item.get("priority", 0),
            )
            for i, item in enumerate(data_list)
        ]

    def get_vlan_protovlan(self) -> list[VLANProtoVLAN]:
        """Get protocol VLAN configuration."""
        raw = self._request("cgi/get_vlan_protovlan_pkd")
        data_list = parse_pipe_array(raw)
        return [
            VLANProtoVLAN(
                vlan_id=item.get("vlan_id", 0),
                proto_id=item.get("proto_id", 0),
                priority=item.get("priority", 0),
            )
            for i, item in enumerate(data_list)
        ]

    def get_oui(self) -> list[OUIEntry]:
        """Get OUI table for voice VLAN."""
        raw = self._request("cgi/get_oui_pkd")
        data_list = parse_pipe_array(raw)
        return [
            OUIEntry(
                oui=item.get("oui", ""),
                vlan_id=item.get("vlan_id", 0),
            )
            for i, item in enumerate(data_list)
        ]

    def get_voice_port(self) -> list[VoicePort]:
        """Get voice port configuration."""
        raw = self._request("cgi/get_voice_port_pkd")
        data_list = parse_pipe_array(raw)
        return [
            VoicePort(
                port=item.get("port", i + 1),
                vlan_id=item.get("vlan_id", 0),
                priority=item.get("priority", 0),
            )
            for i, item in enumerate(data_list)
        ]

    def get_voice_vlan(self) -> list[VoiceVLAN]:
        """Get voice VLAN configuration."""
        raw = self._request("cgi/get_voicevlan_pkd")
        data_list = parse_pipe_array(raw)
        return [
            VoiceVLAN(
                vlan_id=item.get("vlan_id", 0),
                enabled=bool(item.get("enabled", 0)),
                priority=item.get("priority", 0),
            )
            for i, item in enumerate(data_list)
        ]

    # ─── Traffic Endpoints ──────────────────────────────────────────────

    def get_qos_schedule(self) -> QoSSchedule:
        """Get QoS scheduling configuration."""
        data = self._get_parsed("cgi/get_qos_schedule_pkd")
        if isinstance(data, dict):
            return QoSSchedule(
                scheduling_mode=data.get("scheduling_Mode", 1),
                queue_weight_0=data.get("Queue_weight0", 1),
                queue_weight_1=data.get("Queue_weight1", 2),
                queue_weight_2=data.get("Queue_weight2", 4),
                queue_weight_3=data.get("Queue_weight3", 8),
            )
        return QoSSchedule()

    def get_qos_8021p(self) -> list[QoS8021p]:
        """Get 802.1p priority mapping."""
        raw = self._request("cgi/get_qos_8021p_pkd")
        data_list = parse_pipe_array(raw)
        return [
            QoS8021p(
                port=item.get("port", i + 1),
                priority=item.get("priority", 0),
            )
            for i, item in enumerate(data_list)
        ]

    def get_qos_dscp(self) -> list[QoSDSCP]:
        """Get DSCP mapping."""
        raw = self._request("cgi/get_qos_dscp_pkd")
        data_list = parse_pipe_array(raw)
        return [
            QoSDSCP(
                dscp_value=item.get("dscp_value", 0),
                priority=item.get("priority", 0),
            )
            for i, item in enumerate(data_list)
        ]

    def get_qos_port_priority(self) -> list[QoSPortPriority]:
        """Get per-port QoS priority."""
        raw = self._request("cgi/get_qos_port_pkd")
        data_list = parse_pipe_array(raw)
        return [
            QoSPortPriority(
                port=item.get("port", i + 1),
                priority=item.get("priority", 0),
            )
            for i, item in enumerate(data_list)
        ]

    def get_acl_ip(self) -> list[ACLRule]:
        """Get IP ACL rules."""
        raw = self._request("cgi/get_acl_ipacl_pkd")
        data_list = parse_pipe_array(raw)
        return [
            ACLRule(
                rule_id=item.get("rule_id", 0),
                action=item.get("action", ""),
                source_ip=item.get("source_ip", ""),
                dest_ip=item.get("dest_ip", ""),
                source_port=item.get("source_port", 0),
                dest_port=item.get("dest_port", 0),
                protocol=item.get("protocol", 0),
            )
            for i, item in enumerate(data_list)
        ]

    def get_acl_mac(self) -> list[ACLRule]:
        """Get MAC ACL rules."""
        raw = self._request("cgi/get_acl_macacl_pkd")
        data_list = parse_pipe_array(raw)
        return [
            ACLRule(
                rule_id=item.get("rule_id", 0),
                action=item.get("action", ""),
                source_mac=item.get("source_mac", ""),
                dest_mac=item.get("dest_mac", ""),
                protocol=item.get("protocol", 0),
            )
            for i, item in enumerate(data_list)
        ]

    def get_stp_global(self) -> STPGlobal:
        """Get STP global configuration."""
        data = self._get_parsed("cgi/get_stp_global_pkd")
        if isinstance(data, dict):
            return STPGlobal(
                stp_state=data.get("stpstate", 0),
                stp_version=data.get("stpversion", 0),
                bpdu_process=data.get("bpduprocess", 0),
                max_age=data.get("maxage", 20),
                hello_time=data.get("hellotime", 2),
                forward_delay=data.get("forwarddelay", 15),
                max_hops=data.get("maxhops", 20),
                region_root_bridge=data.get("regionrootbridge", ""),
                internal_root_path_cost=data.get("internalrootpathcost", 0),
            )
        return STPGlobal()

    def get_stp_instance(self) -> list[STPInstance]:
        """Get STP MSTP instances."""
        raw = self._request("cgi/get_stp_instance_pkd")
        data_list = parse_pipe_array(raw)
        return [
            STPInstance(
                instance_id=item.get("instance_id", 0),
                vlan_range=item.get("vlan_range", ""),
                root_priority=item.get("root_priority", 0),
            )
            for i, item in enumerate(data_list)
        ]

    def get_stp_port_config(self) -> list[STPPortConfig]:
        """Get STP per-port configuration."""
        raw = self._request("cgi/get_stp_portconfig_pkd")
        data_list = parse_pipe_array(raw)
        return [
            STPPortConfig(
                port=item.get("port", i + 1),
                enabled=bool(item.get("enabled", 0)),
                path_cost=item.get("path_cost", 0),
                priority=item.get("priority", 0),
            )
            for i, item in enumerate(data_list)
        ]

    def get_stp_msti_port_config(self) -> list[STPMSTIPortConfig]:
        """Get STP MSTI per-port configuration."""
        raw = self._request("cgi/get_stp_mstiportconfig_pkd")
        data_list = parse_pipe_array(raw)
        return [
            STPMSTIPortConfig(
                port=item.get("port", i + 1),
                instance_id=item.get("instance_id", 0),
                path_cost=item.get("path_cost", 0),
                priority=item.get("priority", 0),
            )
            for i, item in enumerate(data_list)
        ]

    def get_stp_statistics(self) -> list[STPStatistics]:
        """Get STP statistics."""
        raw = self._request("cgi/get_stp_statistics_pkd")
        data_list = parse_pipe_array(raw)
        return [
            STPStatistics(
                port=item.get("port", i + 1),
                bpdu_sent=item.get("bpdu_sent", 0),
                bpdu_received=item.get("bpdu_received", 0),
                config_sent=item.get("config_sent", 0),
                config_received=item.get("config_received", 0),
            )
            for i, item in enumerate(data_list)
        ]

    def get_igmp_snooping_global(self) -> IGMPGlobal:
        """Get IGMP snooping global configuration."""
        data = self._get_parsed("cgi/get_igmp_snooping_global_pkd")
        if isinstance(data, dict):
            return IGMPGlobal(
                enabled=bool(data.get("enabled", 0)),
                version=data.get("version", 2),
                query_interval=data.get("query_interval", 60),
                max_response_time=data.get("max_response_time", 10),
            )
        return IGMPGlobal()

    def get_igmp_snooping_vlan(self) -> list[IGMPVLAN]:
        """Get IGMP snooping per-VLAN configuration."""
        raw = self._request("cgi/get_igmp_snooping_vlan_pkd")
        data_list = parse_pipe_array(raw)
        return [
            IGMPVLAN(
                vlan_id=item.get("vlan_id", 0),
                enabled=bool(item.get("enabled", 0)),
                version=item.get("version", 2),
            )
            for i, item in enumerate(data_list)
        ]

    def get_igmp_snooping_group(self) -> list[IGMPGroup]:
        """Get IGMP snooping groups."""
        raw = self._request("cgi/get_igmp_snooping_group_pkd")
        data_list = parse_pipe_array(raw)
        return [
            IGMPGroup(
                vlan_id=item.get("vlan_id", 0),
                group_addr=item.get("group_addr", ""),
                port=item.get("port", ""),
            )
            for i, item in enumerate(data_list)
        ]

    def get_igmp_fast_leave(self) -> list[IGMPFastLeave]:
        """Get IGMP fast-leave configuration."""
        raw = self._request("cgi/get_igmp_fastleave_pkd")
        data_list = parse_pipe_array(raw)
        return [
            IGMPFastLeave(
                port=item.get("port", i + 1),
                enabled=bool(item.get("enabled", 0)),
            )
            for i, item in enumerate(data_list)
        ]

    def get_igmp_multicast_filter(self) -> list[IGMPMulticastFilter]:
        """Get IGMP multicast filtering."""
        raw = self._request("cgi/get_igmp_mul_filting_pkd")
        data_list = parse_pipe_array(raw)
        return [
            IGMPMulticastFilter(
                port=item.get("port", i + 1),
                action=item.get("action", ""),
                group_addr=item.get("group_addr", ""),
            )
            for i, item in enumerate(data_list)
        ]

    def get_dhcp_relay(self) -> DHCPRelay:
        """Get DHCP relay configuration."""
        data = self._get_parsed("cgi/get_dhcpRelay_pkd")
        if isinstance(data, dict):
            return DHCPRelay(
                enabled=bool(data.get("enabled", 0)),
                primary_server=data.get("primary_server", ""),
                secondary_server=data.get("secondary_server", ""),
            )
        return DHCPRelay()

    def get_dhcp_service(self) -> DHCPService:
        """Get DHCP service configuration."""
        data = self._get_parsed("cgi/get_dhcpService_pkd")
        if isinstance(data, dict):
            return DHCPService(
                enabled=bool(data.get("enabled", 0)),
                pool_name=data.get("pool_name", ""),
                network=data.get("network", ""),
                gateway=data.get("gateway", ""),
                dns=data.get("dns", ""),
            )
        return DHCPService()

    def get_dhcp_server(self) -> list[dict[str, Any]]:
        """Get DHCP relay server configuration."""
        raw = self._request("cgi/get_server_pkd")
        return parse_pipe_array(raw)

    def get_dhcp_snooping_global(self) -> DHCPSnoopingGlobal:
        """Get DHCP snooping global configuration."""
        data = self._get_parsed("cgi/get_dhcpsnooping_global_pkd")
        if isinstance(data, dict):
            return DHCPSnoopingGlobal(
                enabled=bool(data.get("enabled", 0)),
            )
        return DHCPSnoopingGlobal()

    def get_dhcp_snooping_port(self) -> list[DHCPSnoopingPort]:
        """Get DHCP snooping per-port configuration."""
        raw = self._request("cgi/get_dhcpsnooping_port_pkd")
        data_list = parse_pipe_array(raw)
        return [
            DHCPSnoopingPort(
                port=item.get("port", i + 1),
                enabled=bool(item.get("enabled", 0)),
                trust=bool(item.get("trust", 0)),
            )
            for i, item in enumerate(data_list)
        ]

    def get_dhcp_snooping_users(self) -> list[DHCPSnoopingUser]:
        """Get DHCP snooping user bindings."""
        raw = self._request("cgi/get_dhcpsnooping_users_pkd")
        data_list = parse_pipe_array(raw)
        return [
            DHCPSnoopingUser(
                mac=item.get("mac", ""),
                ip=item.get("ip", ""),
                vlan=item.get("vlan", 0),
                port=item.get("port", ""),
            )
            for i, item in enumerate(data_list)
        ]

    # ─── Security Endpoints ─────────────────────────────────────────────

    def get_arp_defense(self) -> list[ARPDefense]:
        """Get ARP defense configuration."""
        raw = self._request("cgi/get_arpLimit_pkd")
        data_list = parse_pipe_array(raw)
        return [
            ARPDefense(
                port=item.get("port", i + 1),
                enabled=bool(item.get("enabled", 0)),
                max_arp=item.get("max_arp", 0),
            )
            for i, item in enumerate(data_list)
        ]

    def get_worm_defense(self) -> WormDefense:
        """Get worm defense configuration."""
        data = self._get_parsed("cgi/get_wormLimit_pkd")
        if isinstance(data, dict):
            return WormDefense(
                enabled=bool(data.get("enabled", 0)),
                threshold=data.get("threshold", 0),
            )
        return WormDefense()

    def get_dos_defense(self) -> DOSDefense:
        """Get DoS defense configuration."""
        data = self._get_parsed("cgi/get_dosLimit_pkd")
        if isinstance(data, dict):
            return DOSDefense(
                enabled=bool(data.get("enabled", 0)),
                threshold=data.get("threshold", 0),
            )
        return DOSDefense()

    def get_mac_defense(self) -> list[MACDefense]:
        """Get MAC defense configuration."""
        raw = self._request("cgi/get_macLimit_pkd")
        data_list = parse_pipe_array(raw)
        return [
            MACDefense(
                port=item.get("port", i + 1),
                enabled=bool(item.get("enabled", 0)),
                max_mac=item.get("max_mac", 0),
            )
            for i, item in enumerate(data_list)
        ]

    def get_sec_filter(self) -> list[SecFilter]:
        """Get security filter configuration."""
        raw = self._request("cgi/get_secFilter_pkd")
        data_list = parse_pipe_array(raw)
        return [
            SecFilter(
                port=item.get("port", i + 1),
                enabled=bool(item.get("enabled", 0)),
                filter_type=item.get("filter_type", ""),
            )
            for i, item in enumerate(data_list)
        ]

    def get_sec_impb(self) -> SecImpb:
        """Get import/export bind configuration."""
        data = self._get_parsed("cgi/get_sec_impb_pkd")
        if isinstance(data, dict):
            return SecImpb(
                enabled=bool(data.get("enabled", 0)),
            )
        return SecImpb()

    def get_sec_onekeybind(self) -> SecOneKeyBind:
        """Get one-key bind configuration."""
        data = self._get_parsed("cgi/get_sec_onekeybind_pkd")
        if isinstance(data, dict):
            return SecOneKeyBind(
                enabled=bool(data.get("enabled", 0)),
            )
        return SecOneKeyBind()

    def get_mac_filter(self) -> MACFilter:
        """Get MAC filtering configuration."""
        data = self._get_parsed("cgi/get_mac_filtrate_pkd")
        if isinstance(data, dict):
            return MACFilter(
                enabled=bool(data.get("enabled", 0)),
                filter_type=data.get("filter_type", ""),
            )
        return MACFilter()

    def get_dot1x_global(self) -> Dot1XGlobal:
        """Get 802.1X global configuration."""
        data = self._get_parsed("cgi/get_dot1x_global_pkd")
        if isinstance(data, dict):
            return Dot1XGlobal(
                enabled=bool(data.get("enabled", 0)),
                auth_method=data.get("auth_method", ""),
            )
        return Dot1XGlobal()

    def get_dot1x_frame(self) -> Dot1XFrame:
        """Get 802.1X frame counter."""
        data = self._get_parsed("cgi/get_dot1x_frame_pkd")
        if isinstance(data, dict):
            return Dot1XFrame(
                success=data.get("success", 0),
                failed=data.get("failed", 0),
                timeout=data.get("timeout", 0),
            )
        return Dot1XFrame()

    # ─── Management Endpoints ───────────────────────────────────────────

    def get_snmp_agent(self) -> SNMPAgent:
        """Get SNMP agent configuration."""
        data = self._get_parsed("cgi/get_snmp_agent_pkd")
        if isinstance(data, dict):
            return SNMPAgent(
                community_name=data.get("communityName", ""),
                view_name=data.get("viewName", ""),
                access_right=data.get("accessRight", 0),
            )
        return SNMPAgent()

    def get_snmp_group(self) -> list[SNMPGroup]:
        """Get SNMP groups."""
        raw = self._request("cgi/get_snmp_groupconfig_pkd")
        data_list = parse_pipe_array(raw)
        return [
            SNMPGroup(
                group_name=item.get("group_name", ""),
                security_model=item.get("security_model", ""),
                security_level=item.get("security_level", ""),
            )
            for i, item in enumerate(data_list)
        ]

    def get_snmp_user(self) -> list[SNMPUser]:
        """Get SNMP users."""
        raw = self._request("cgi/get_snmp_userconfig_pkd")
        data_list = parse_pipe_array(raw)
        return [
            SNMPUser(
                username=item.get("username", ""),
                group=item.get("group", ""),
                auth_protocol=item.get("auth_protocol", ""),
                priv_protocol=item.get("priv_protocol", ""),
            )
            for i, item in enumerate(data_list)
        ]

    def get_snmp_view(self) -> list[SNMPView]:
        """Get SNMP views."""
        raw = self._request("cgi/get_snmp_viewconfig_pkd")
        data_list = parse_pipe_array(raw)
        return [
            SNMPView(
                view_name=item.get("view_name", ""),
                subtree=item.get("subtree", ""),
                included=bool(item.get("included", True)),
            )
            for i, item in enumerate(data_list)
        ]

    def get_snmp_trap(self) -> SNMPTrap:
        """Get SNMP trap configuration."""
        data = self._get_parsed("cgi/get_snmp_trapconfig_pkd")
        if isinstance(data, dict):
            return SNMPTrap(
                enabled=bool(data.get("enabled", 0)),
                server=data.get("server", ""),
                port=data.get("port", 162),
                community=data.get("community", ""),
            )
        return SNMPTrap()

    def get_lldp_global(self) -> LLDPGlobal:
        """Get LLDP global configuration."""
        data = self._get_parsed("cgi/get_lldp_global_pkd")
        if isinstance(data, dict):
            return LLDPGlobal(
                enabled=bool(data.get("enabled", 0)),
            )
        return LLDPGlobal()

    def get_lldp_port(self) -> list[LLDPPort]:
        """Get LLDP per-port configuration."""
        raw = self._request("cgi/get_lldp_port_pkd")
        data_list = parse_pipe_array(raw)
        return [
            LLDPPort(
                port=item.get("port", i + 1),
                enabled=bool(item.get("enabled", 0)),
            )
            for i, item in enumerate(data_list)
        ]

    def get_lldp_neighbor(self) -> list[LLDPNeighbor]:
        """Get LLDP neighbors."""
        raw = self._request("cgi/get_lldp_neighbor_pkd")
        data_list = parse_pipe_array(raw)
        return [
            LLDPNeighbor(
                port_no=item.get("portNo", ""),
                chassis_id=item.get("chassisid", ""),
                telnet_no=item.get("telnetno", ""),
                sys_name=item.get("sysname", ""),
                port_desc=item.get("portdescri", ""),
                capability=item.get("capability", ""),
                mgmt_addr=item.get("mngaddr", ""),
            )
            for i, item in enumerate(data_list)
        ]

    def get_lldp_statistics(self) -> list[LLDPStatistic]:
        """Get LLDP statistics."""
        raw = self._request("cgi/get_lldp_statistic_pkd")
        data_list = parse_pipe_array(raw)
        return [
            LLDPStatistic(
                port=item.get("port", i + 1),
                tx_frames=item.get("tx_frames", 0),
                rx_frames=item.get("rx_frames", 0),
            )
            for i, item in enumerate(data_list)
        ]

    def get_syslog_log(self) -> list[SyslogLog]:
        """Get syslog log entries."""
        raw = self._request("cgi/get_syslog_log_pkd")
        data_list = parse_pipe_array(raw)
        return [
            SyslogLog(
                timestamp=item.get("timestamp", ""),
                severity=item.get("severity", ""),
                message=item.get("message", ""),
            )
            for i, item in enumerate(data_list)
        ]

    def get_syslog_server(self) -> SyslogServer:
        """Get syslog server configuration."""
        data = self._get_parsed("cgi/get_syslog_server_pkd")
        if isinstance(data, dict):
            return SyslogServer(
                server=data.get("server", ""),
                port=data.get("port", 514),
                enabled=bool(data.get("enabled", 0)),
            )
        return SyslogServer()

    def get_cable_diag(self) -> list[CableDiag]:
        """Get cable diagnostics results."""
        raw = self._request("cgi/get_cable_diag_pkd")
        data_list = parse_pipe_array(raw)
        return [
            CableDiag(
                port=item.get("port", 0),
                status=item.get("status", ""),
                distance=item.get("distance", ""),
            )
            for i, item in enumerate(data_list)
        ]

    def get_ping_diag(self) -> PingDiag:
        """Get ping diagnostics result."""
        data = self._get_parsed("cgi/get_ping_diag_pkd")
        if isinstance(data, dict):
            return PingDiag(
                target=data.get("target", ""),
                packets_sent=data.get("packets_sent", 0),
                packets_received=data.get("packets_received", 0),
                loss_pct=data.get("loss_pct", ""),
                rtt_min=data.get("rtt_min", ""),
                rtt_avg=data.get("rtt_avg", ""),
                rtt_max=data.get("rtt_max", ""),
            )
        return PingDiag()

    def get_tracert_diag(self) -> TracertDiag:
        """Get tracert diagnostics result."""
        data = self._get_parsed("cgi/get_tracert_diag_pkd")
        if isinstance(data, dict):
            return TracertDiag(
                target=data.get("target", ""),
                hops=data.get("hops", []),
            )
        return TracertDiag()

    def get_timerange(self) -> list[TimerangeEntry]:
        """Get time range entries."""
        raw = self._request("cgi/get_timerange_pkd")
        data_list = parse_pipe_array(raw)
        return [
            TimerangeEntry(
                name=item.get("name", ""),
                start=item.get("start", ""),
                end=item.get("end", ""),
            )
            for i, item in enumerate(data_list)
        ]

    def get_all_timerange(self) -> list[TimerangeEntry]:
        """Get all time range entries (used by PoE, ACL, etc.)."""
        raw = self._request("cgi/get_all_timerange_pkd")
        data_list = parse_pipe_array(raw)
        return [
            TimerangeEntry(
                name=item.get("name", ""),
                start=item.get("start", ""),
                end=item.get("end", ""),
            )
            for i, item in enumerate(data_list)
        ]

    def get_system_server(self) -> dict[str, Any]:
        """Get system server configuration (for firmware upload)."""
        return self._get_parsed("cgi/get_system_server_pkd")

    # ─── Firmware Endpoints ─────────────────────────────────────────────

    def get_firmware_info(self) -> FirmwareInfo:
        """Get firmware version and update availability."""
        raw = self._request("cgi/cloudfu_basicInfo_pkd")
        data = parse_quoted_object(raw)
        return FirmwareInfo(
            version=data.get("firmVersion", "unknown"),
            update_available=bool(data.get("update", False)),
        )

    def check_session(self) -> bool:
        """Check if the session is still valid.

        Returns True if the session is alive, False if expired.
        """
        try:
            raw = self._request("cgi/check_timeout_pkd")
            return raw.strip() != "20"
        except PakedgeSessionExpired:
            return False
        except PakedgeError:
            return False

    def __enter__(self) -> PakedgeClient:
        self.login()
        return self

    def __exit__(self, *args: Any) -> None:
        self.logout()

    def __repr__(self) -> str:
        status = "logged in" if self._logged_in else "not logged in"
        return f"<PakedgeClient host={self.host} {status}>"
