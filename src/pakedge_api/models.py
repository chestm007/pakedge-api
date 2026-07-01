"""Dataclasses for PakEdge API responses."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PortStatus:
    """Port basic info (link status, PVID)."""
    port: int
    state: int  # 0=link, 1=link up
    linkstatus: int  # 0=off, 1=up
    pvid: int


@dataclass
class PortConfig:
    """Port configuration."""
    port: int
    linkstatus: int
    state: int
    autocfg: int  # auto-negotiation
    port_type: int
    pvid: int
    jumbo: int  # MTU


@dataclass
class PortStatistics:
    """Port statistics counters."""
    port: int
    rx_octets: int = 0
    rx_unicast_pkts: int = 0
    rx_nonunicast_pkts: int = 0
    rx_errors: int = 0
    rx_discard: int = 0
    tx_octets: int = 0
    tx_unicast_pkts: int = 0
    tx_nonunicast_pkts: int = 0
    tx_errors: int = 0
    tx_discard: int = 0


@dataclass
class FirmwareInfo:
    """Firmware version and update status."""
    version: str
    update_available: bool = False


@dataclass
class SystemInfo:
    """System information."""
    description: str = ""
    version: str = ""
    product_intf: int = 0
    uptime: int = 0
    name: str = ""
    location: str = ""
    management_vlan: int = 0
    mac_age: int = 0
    login_timeout: int = 0
    dhcp_enabled: bool = False
    ip_address: str = ""
    gateway: str = ""
    dns: str = ""


@dataclass
class SystemTime:
    """System time configuration."""
    current_time: str = ""
    timezone: str = ""
    sntp_state: int = 0
    primary_server: str = ""
    secondary_server: str = ""
    poll_time: int = 0


@dataclass
class SystemUser:
    """System user account."""
    username: str = ""
    privilege: int = 0


@dataclass
class SystemStatus:
    """System resource status."""
    cpu_usage: str = ""
    memory_usage: str = ""
    temperature: str = ""


@dataclass
class IPConfig:
    """IP configuration."""
    ip_address: str = ""
    subnet_mask: str = ""
    gateway: str = ""
    dns: str = ""


@dataclass
class VLANSetting:
    """VLAN settings."""
    vlan_type: int = 1


@dataclass
class STPGlobal:
    """STP global configuration."""
    stp_state: int = 0
    stp_version: int = 0
    bpdu_process: int = 0
    max_age: int = 20
    hello_time: int = 2
    forward_delay: int = 15
    max_hops: int = 20
    region_root_bridge: str = ""
    internal_root_path_cost: int = 0


@dataclass
class LLDPNeighbor:
    """LLDP neighbor information."""
    port_no: str = ""
    chassis_id: str = ""
    telnet_no: str = ""
    sys_name: str = ""
    port_desc: str = ""
    capability: str = ""
    mgmt_addr: str = ""


@dataclass
class PoEGlobal:
    """PoE global configuration."""
    power_mgmt_mode: int = 0
    usage_ratio: str = ""
    chip_temp: str = ""


@dataclass
class QoSSchedule:
    """QoS scheduling configuration."""
    scheduling_mode: int = 1
    queue_weight_0: int = 1
    queue_weight_1: int = 2
    queue_weight_2: int = 4
    queue_weight_3: int = 8


@dataclass
class SNMPAgent:
    """SNMP agent configuration."""
    community_name: str = ""
    view_name: str = ""
    access_right: int = 0


@dataclass
class SyslogLog:
    """Syslog log entry."""
    timestamp: str = ""
    severity: str = ""
    message: str = ""


@dataclass
class CableDiag:
    """Cable diagnostics result."""
    port: int = 0
    status: str = ""
    distance: str = ""


@dataclass
class PingDiag:
    """Ping diagnostics result."""
    target: str = ""
    packets_sent: int = 0
    packets_received: int = 0
    loss_pct: str = ""
    rtt_min: str = ""
    rtt_avg: str = ""
    rtt_max: str = ""


@dataclass
class TracertDiag:
    """Tracert diagnostics result."""
    target: str = ""
    hops: list[str] = None  # noqa: RUF012

    def __post_init__(self) -> None:
        if self.hops is None:
            self.hops = []


@dataclass
class MirrorConfig:
    """Port mirroring configuration."""
    mirror_type: int = 0
    source_port: str = ""
    destination_port: str = ""


@dataclass
class TrunkAggr:
    """Link aggregation configuration."""
    group_id: int = 0
    ports: str = ""
    mode: int = 0


@dataclass
class TrunkLACP:
    """LACP aggregation configuration."""
    group_id: int = 0
    ports: str = ""
    system_priority: int = 0
    port_priority: int = 0
    key: int = 0


@dataclass
class MACAddress:
    """MAC address entry."""
    port: str = ""
    mac: str = ""
    vlan: int = 0
    type: str = ""  # dynamic, static


@dataclass
class MACStatic:
    """Static MAC address entry."""
    mac: str = ""
    port: str = ""
    vlan: int = 0


@dataclass
class PortFlowControl:
    """Port flow control configuration."""
    port: int = 0
    rx_enabled: bool = False
    tx_enabled: bool = False


@dataclass
class PortStormControl:
    """Broadcast/multicast/unicast storm control."""
    port: int = 0
    bc_rate: int = 0
    mc_rate: int = 0
    uc_rate: int = 0


@dataclass
class PortRateLimit:
    """Port rate limiting configuration."""
    port: int = 0
    rx_rate: int = 0
    tx_rate: int = 0


@dataclass
class PoEPort:
    """Per-port PoE configuration."""
    port: int = 0
    enabled: bool = False
    priority: int = 0
    max_power: int = 0
    actual_power: int = 0
    status: str = ""


@dataclass
class Dot1XPort:
    """802.1X port configuration."""
    port: int = 0
    enabled: bool = False
    mode: str = ""


@dataclass
class VLANAccessPort:
    """Access port VLAN configuration."""
    port: int = 0
    pvid: int = 1
    member_type: str = "untagged"


@dataclass
class VLANTrunkPort:
    """Trunk port VLAN configuration."""
    port: int = 0
    pvid: int = 1
    allowed_vlans: str = ""
    native_vlan: int = 1


@dataclass
class VLANHybridPort:
    """Hybrid port VLAN configuration."""
    port: int = 0
    pvid: int = 1
    tagged_vlans: str = ""
    untagged_vlans: str = ""


@dataclass
class VLANMAC:
    """MAC-based VLAN entry."""
    vlan_id: int = 0
    mac: str = ""
    priority: int = 0


@dataclass
class VLANProtocol:
    """Protocol-based VLAN entry."""
    vlan_id: int = 0
    protocol: str = ""
    priority: int = 0


@dataclass
class VLANProtoVLAN:
    """Protocol VLAN configuration."""
    vlan_id: int = 0
    proto_id: int = 0
    priority: int = 0


@dataclass
class OUIEntry:
    """OUI table entry for voice VLAN."""
    oui: str = ""
    vlan_id: int = 0


@dataclass
class VoicePort:
    """Voice port configuration."""
    port: int = 0
    vlan_id: int = 0
    priority: int = 0


@dataclass
class VoiceVLAN:
    """Voice VLAN configuration."""
    vlan_id: int = 0
    enabled: bool = False
    priority: int = 0


@dataclass
class QoS8021p:
    """802.1p priority mapping."""
    port: int = 0
    priority: int = 0


@dataclass
class QoSDSCP:
    """DSCP mapping."""
    dscp_value: int = 0
    priority: int = 0


@dataclass
class QoSPortPriority:
    """Per-port QoS priority."""
    port: int = 0
    priority: int = 0


@dataclass
class ACLRule:
    """ACL rule."""
    rule_id: int = 0
    action: str = ""  # permit, deny
    source_ip: str = ""
    dest_ip: str = ""
    source_port: int = 0
    dest_port: int = 0
    protocol: int = 0


@dataclass
class STPInstance:
    """STP MSTP instance."""
    instance_id: int = 0
    vlan_range: str = ""
    root_priority: int = 0


@dataclass
class STPPortConfig:
    """STP per-port configuration."""
    port: int = 0
    enabled: bool = False
    path_cost: int = 0
    priority: int = 0


@dataclass
class STPMSTIPortConfig:
    """STP MSTI per-port configuration."""
    port: int = 0
    instance_id: int = 0
    path_cost: int = 0
    priority: int = 0


@dataclass
class STPStatistics:
    """STP statistics."""
    port: int = 0
    bpdu_sent: int = 0
    bpdu_received: int = 0
    config_sent: int = 0
    config_received: int = 0


@dataclass
class IGMPGlobal:
    """IGMP snooping global configuration."""
    enabled: bool = False
    version: int = 2
    query_interval: int = 60
    max_response_time: int = 10


@dataclass
class IGMPVLAN:
    """IGMP snooping per-VLAN configuration."""
    vlan_id: int = 0
    enabled: bool = False
    version: int = 2


@dataclass
class IGMPGroup:
    """IGMP snooping group."""
    vlan_id: int = 0
    group_addr: str = ""
    port: str = ""


@dataclass
class IGMPFastLeave:
    """IGMP fast-leave configuration."""
    port: int = 0
    enabled: bool = False


@dataclass
class IGMPMulticastFilter:
    """IGMP multicast filtering."""
    port: int = 0
    action: str = ""  # permit, deny
    group_addr: str = ""


@dataclass
class DHCPRelay:
    """DHCP relay configuration."""
    enabled: bool = False
    primary_server: str = ""
    secondary_server: str = ""


@dataclass
class DHCPService:
    """DHCP service configuration."""
    enabled: bool = False
    pool_name: str = ""
    network: str = ""
    gateway: str = ""
    dns: str = ""


@dataclass
class DHCPSnoopingGlobal:
    """DHCP snooping global configuration."""
    enabled: bool = False


@dataclass
class DHCPSnoopingPort:
    """DHCP snooping per-port configuration."""
    port: int = 0
    enabled: bool = False
    trust: bool = False


@dataclass
class DHCPSnoopingUser:
    """DHCP snooping user binding."""
    mac: str = ""
    ip: str = ""
    vlan: int = 0
    port: str = ""


@dataclass
class ARPDefense:
    """ARP defense configuration."""
    port: int = 0
    enabled: bool = False
    max_arp: int = 0


@dataclass
class WormDefense:
    """Worm defense configuration."""
    enabled: bool = False
    threshold: int = 0


@dataclass
class DOSDefense:
    """DoS defense configuration."""
    enabled: bool = False
    threshold: int = 0


@dataclass
class MACDefense:
    """MAC defense configuration."""
    port: int = 0
    enabled: bool = False
    max_mac: int = 0


@dataclass
class PortFilter:
    """Port filter configuration."""
    port: int = 0
    enabled: bool = False
    filter_type: str = ""


@dataclass
class MACFilter:
    """MAC filtering configuration."""
    enabled: bool = False
    filter_type: str = ""  # permit, deny


@dataclass
class Dot1XGlobal:
    """802.1X global configuration."""
    enabled: bool = False
    auth_method: str = ""


@dataclass
class Dot1XFrame:
    """802.1X frame counter."""
    success: int = 0
    failed: int = 0
    timeout: int = 0


@dataclass
class SNMPGroup:
    """SNMP group configuration."""
    group_name: str = ""
    security_model: str = ""
    security_level: str = ""


@dataclass
class SNMPUser:
    """SNMP user configuration."""
    username: str = ""
    group: str = ""
    auth_protocol: str = ""
    priv_protocol: str = ""


@dataclass
class SNMPView:
    """SNMP view configuration."""
    view_name: str = ""
    subtree: str = ""
    included: bool = True


@dataclass
class SNMPTrap:
    """SNMP trap configuration."""
    enabled: bool = False
    server: str = ""
    port: int = 162
    community: str = ""


@dataclass
class LLDPGlobal:
    """LLDP global configuration."""
    enabled: bool = False


@dataclass
class LLDPPort:
    """LLDP per-port configuration."""
    port: int = 0
    enabled: bool = False


@dataclass
class LLDPStatistic:
    """LLDP statistics."""
    port: int = 0
    tx_frames: int = 0
    rx_frames: int = 0


@dataclass
class SyslogServer:
    """Syslog server configuration."""
    server: str = ""
    port: int = 514
    enabled: bool = False


@dataclass
class SyslogLogConfig:
    """Syslog log configuration."""
    enabled: bool = False
    level: str = ""


@dataclass
class SSLConfig:
    """SSL/TLS configuration."""
    enabled: bool = False
    cert_subject: str = ""
    cert_expiry: str = ""


@dataclass
class SysTimeRange:
    """Time range configuration."""
    name: str = ""
    start_time: str = ""
    end_time: str = ""
    days: str = ""


@dataclass
class TimerangeEntry:
    """Time range entry."""
    name: str = ""
    start: str = ""
    end: str = ""


@dataclass
class SecFilter:
    """Security filter configuration."""
    enabled: bool = False
    filter_type: str = ""


@dataclass
class SecImpb:
    """Import/export bind configuration."""
    enabled: bool = False


@dataclass
class SecOneKeyBind:
    """One-key bind configuration."""
    enabled: bool = False
