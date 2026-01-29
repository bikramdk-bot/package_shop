# Pi Change Report
- Generated: 2026-01-29T08:51:44+01:00


**OS**
Linux packetshop 6.12.47+rpt-rpi-v7 #1 SMP Raspbian 1:6.12.47-1+rpt1 (2025-09-16) armv7l GNU/Linux

 Static hostname: packetshop
       Icon name: computer
      Machine ID: a44addd581ee4594a991ba101c88c59b
         Boot ID: c86a07f18de4413993d2e1a6ac45c231
Operating System: Raspbian GNU/Linux 13 (trixie)
          Kernel: Linux 6.12.47+rpt-rpi-v7
    Architecture: arm

PRETTY_NAME="Raspbian GNU/Linux 13 (trixie)"
NAME="Raspbian GNU/Linux"
VERSION_ID="13"
VERSION="13 (trixie)"
VERSION_CODENAME=trixie
DEBIAN_VERSION_FULL=13.1
ID=raspbian
ID_LIKE=debian
HOME_URL="http://www.raspbian.org/"
SUPPORT_URL="http://www.raspbian.org/RaspbianForums"
BUG_REPORT_URL="http://www.raspbian.org/RaspbianBugs"

**Uptime**
         system boot  2026-01-28 22:12

**Network Interfaces & IPs**
lo               UNKNOWN        00:00:00:00:00:00 <LOOPBACK,UP,LOWER_UP> 
eth0             UP             b8:27:eb:04:9c:95 <BROADCAST,MULTICAST,UP,LOWER_UP> 
wlan0            DOWN           b8:27:eb:51:c9:c0 <BROADCAST,MULTICAST> 
wlan1            UP             40:a5:ef:56:dc:6a <BROADCAST,MULTICAST,UP,LOWER_UP> 

lo               UNKNOWN        127.0.0.1/8 ::1/128 
eth0             UP             10.0.0.64/24 fe80::1c9b:bcef:9ef9:98d/64 
wlan0            DOWN           
wlan1            UP             10.10.0.1/24 fe80::42a5:efff:fe56:dc6a/64 

**Wireless (WLAN)**
rfkill:
0: hci0: Bluetooth
	Soft blocked: yes
	Hard blocked: no
1: phy0: Wireless LAN
	Soft blocked: no
	Hard blocked: no
2: phy1: Wireless LAN
	Soft blocked: no
	Hard blocked: no

iw reg get:
global
country DK: DFS-ETSI
	(2400 - 2483 @ 40), (N/A, 20), (N/A)
	(5150 - 5250 @ 80), (N/A, 23), (N/A), NO-OUTDOOR, AUTO-BW
	(5250 - 5350 @ 80), (N/A, 20), (0 ms), NO-OUTDOOR, DFS, AUTO-BW
	(5470 - 5725 @ 160), (N/A, 26), (0 ms), DFS
	(5725 - 5875 @ 80), (N/A, 13), (N/A)
	(5945 - 6425 @ 320), (N/A, 23), (N/A), NO-OUTDOOR
	(57000 - 66000 @ 2160), (N/A, 40), (N/A)

phy#0
country 99: DFS-UNSET
	(2402 - 2482 @ 40), (6, 20), (N/A)
	(2474 - 2494 @ 20), (6, 20), (N/A)
	(5140 - 5360 @ 160), (6, 20), (N/A)
	(5460 - 5860 @ 160), (6, 20), (N/A)


iw list (caps):
Wiphy phy1
	wiphy index: 1
	max # scan SSIDs: 4
	max scan IEs length: 2243 bytes
	max # sched scan SSIDs: 0
	max # match sets: 0
	Retry short limit: 7
	Retry long limit: 4
	Coverage class: 0 (up to 0m)
	Device supports RSN-IBSS.
	Device supports AP-side u-APSD.
	Device supports T-DLS.
	Supported Ciphers:
		* WEP40 (00-0f-ac:1)
		* WEP104 (00-0f-ac:5)
		* TKIP (00-0f-ac:2)
		* CCMP-128 (00-0f-ac:4)
		* CCMP-256 (00-0f-ac:10)
		* GCMP-128 (00-0f-ac:8)
		* GCMP-256 (00-0f-ac:9)
		* CMAC (00-0f-ac:6)
		* CMAC-256 (00-0f-ac:13)
		* GMAC-128 (00-0f-ac:11)
		* GMAC-256 (00-0f-ac:12)
	Available Antennas: TX 0x3 RX 0x3
	Configured Antennas: TX 0x3 RX 0x3
	Supported interface modes:
		 * IBSS
		 * managed
		 * AP
		 * AP/VLAN
		 * monitor
		 * mesh point
		 * P2P-client
		 * P2P-GO
	Band 1:
		Capabilities: 0x1ff
			RX LDPC
			HT20/HT40
			SM Power Save disabled
			RX Greenfield
			RX HT20 SGI
			RX HT40 SGI
			TX STBC
			RX STBC 1-stream
			Max AMSDU length: 3839 bytes
			No DSSS/CCK HT40
		Maximum RX AMPDU length 65535 bytes (exponent: 0x003)
		Minimum RX AMPDU time spacing: No restriction (0x00)
		HT TX/RX MCS rate indexes supported: 0-15
		Bitrates (non-HT):
			* 1.0 Mbps (short preamble supported)
			* 2.0 Mbps (short preamble supported)
			* 5.5 Mbps (short preamble supported)
			* 11.0 Mbps (short preamble supported)
			* 6.0 Mbps
			* 9.0 Mbps
			* 12.0 Mbps
			* 18.0 Mbps
			* 24.0 Mbps
			* 36.0 Mbps
			* 48.0 Mbps
			* 54.0 Mbps
		Frequencies:
			* 2412.0 MHz [1] (20.0 dBm)
			* 2417.0 MHz [2] (20.0 dBm)
			* 2422.0 MHz [3] (20.0 dBm)
			* 2427.0 MHz [4] (20.0 dBm)
			* 2432.0 MHz [5] (20.0 dBm)
			* 2437.0 MHz [6] (20.0 dBm)
			* 2442.0 MHz [7] (20.0 dBm)
			* 2447.0 MHz [8] (20.0 dBm)
			* 2452.0 MHz [9] (20.0 dBm)
			* 2457.0 MHz [10] (20.0 dBm)
			* 2462.0 MHz [11] (20.0 dBm)
			* 2467.0 MHz [12] (20.0 dBm)
			* 2472.0 MHz [13] (20.0 dBm)
			* 2484.0 MHz [14] (disabled)
	Band 2:
		Capabilities: 0x1ff
			RX LDPC
			HT20/HT40
			SM Power Save disabled
			RX Greenfield
			RX HT20 SGI
			RX HT40 SGI
			TX STBC
			RX STBC 1-stream
			Max AMSDU length: 3839 bytes
			No DSSS/CCK HT40
		Maximum RX AMPDU length 65535 bytes (exponent: 0x003)
		Minimum RX AMPDU time spacing: No restriction (0x00)
		HT TX/RX MCS rate indexes supported: 0-15
		VHT Capabilities (0x318001b0):
			Max MPDU length: 3895
			Supported Channel Width: neither 160 nor 80+80
			RX LDPC
			short GI (80 MHz)
			TX STBC
			RX antenna pattern consistency
			TX antenna pattern consistency
		VHT RX MCS set:
			1 streams: MCS 0-9
			2 streams: MCS 0-9
			3 streams: not supported
			4 streams: not supported
			5 streams: not supported
			6 streams: not supported
			7 streams: not supported
			8 streams: not supported
		VHT RX highest supported: 0 Mbps
		VHT TX MCS set:
			1 streams: MCS 0-9
			2 streams: MCS 0-9
			3 streams: not supported
			4 streams: not supported
			5 streams: not supported
			6 streams: not supported
			7 streams: not supported
			8 streams: not supported
		VHT TX highest supported: 0 Mbps
		VHT extended NSS: not supported
		Bitrates (non-HT):
			* 6.0 Mbps
			* 9.0 Mbps
			* 12.0 Mbps
			* 18.0 Mbps
			* 24.0 Mbps
			* 36.0 Mbps
			* 48.0 Mbps
			* 54.0 Mbps
		Frequencies:
			* 5180.0 MHz [36] (20.0 dBm)
			* 5200.0 MHz [40] (20.0 dBm)
			* 5220.0 MHz [44] (20.0 dBm)
			* 5240.0 MHz [48] (20.0 dBm)
			* 5260.0 MHz [52] (20.0 dBm) (radar detection)
			* 5280.0 MHz [56] (20.0 dBm) (radar detection)
			* 5300.0 MHz [60] (20.0 dBm) (radar detection)
			* 5320.0 MHz [64] (20.0 dBm) (radar detection)
			* 5500.0 MHz [100] (20.0 dBm) (radar detection)
			* 5520.0 MHz [104] (20.0 dBm) (radar detection)
			* 5540.0 MHz [108] (20.0 dBm) (radar detection)
			* 5560.0 MHz [112] (20.0 dBm) (radar detection)
			* 5580.0 MHz [116] (20.0 dBm) (radar detection)
			* 5600.0 MHz [120] (20.0 dBm) (radar detection)
			* 5620.0 MHz [124] (20.0 dBm) (radar detection)
			* 5640.0 MHz [128] (20.0 dBm) (radar detection)
			* 5660.0 MHz [132] (20.0 dBm) (radar detection)
			* 5680.0 MHz [136] (20.0 dBm) (radar detection)
			* 5700.0 MHz [140] (20.0 dBm) (radar detection)
			* 5720.0 MHz [144] (13.0 dBm) (radar detection)
			* 5745.0 MHz [149] (13.0 dBm)
			* 5765.0 MHz [153] (13.0 dBm)
			* 5785.0 MHz [157] (13.0 dBm)
			* 5805.0 MHz [161] (13.0 dBm)
			* 5825.0 MHz [165] (13.0 dBm)
			* 5845.0 MHz [169] (13.0 dBm)
			* 5865.0 MHz [173] (13.0 dBm)
			* 5885.0 MHz [177] (disabled)
	Supported commands:
		 * new_interface
		 * set_interface
		 * new_key
		 * start_ap
		 * new_station
		 * new_mpath
		 * set_mesh_config
		 * set_bss
		 * authenticate
		 * associate
		 * deauthenticate
		 * disassociate
		 * join_ibss
		 * join_mesh
		 * remain_on_channel
		 * set_tx_bitrate_mask
		 * frame
		 * frame_wait_cancel
		 * set_wiphy_netns
		 * set_channel
		 * tdls_mgmt
		 * tdls_oper
		 * probe_client
		 * set_noack_map
		 * register_beacons
		 * start_p2p_device
		 * set_mcast_rate
		 * connect
		 * disconnect
		 * channel_switch
		 * set_qos_map
		 * set_multicast_to_unicast
		 * set_sar_specs
	software interface modes (can always be added):
		 * AP/VLAN
		 * monitor
	valid interface combinations:
		 * #{ IBSS } <= 1, #{ managed, AP, mesh point, P2P-client, P2P-GO } <= 2,
		   total <= 2, #channels <= 1, STA/AP BI must match
	HT Capability overrides:
		 * MCS: ff ff ff ff ff ff ff ff ff ff
		 * maximum A-MSDU length
		 * supported channel width
		 * short GI for 40 MHz
		 * max A-MPDU length exponent
		 * min MPDU start spacing
	Device supports TX status socket option.
	Device supports HT-IBSS.
	Device supports SAE with AUTHENTICATE command
	Device supports low priority scan.
	Device supports scan flush.
	Device supports AP scan.
	Device supports per-vif TX power setting
	Driver supports full state transitions for AP/GO clients
	Driver supports a userspace MPM
	Device supports active monitor (which will ACK incoming frames)
	Driver/device bandwidth changes during BSS lifetime (AP/GO mode)
	Device supports configuring vdev MAC-addr on create.
	max # scan plans: 1
	max scan plan interval: -1
	max scan plan iterations: 0
	Supported TX frame types:
		 * IBSS: 0x00 0x10 0x20 0x30 0x40 0x50 0x60 0x70 0x80 0x90 0xa0 0xb0 0xc0 0xd0 0xe0 0xf0
		 * managed: 0x00 0x10 0x20 0x30 0x40 0x50 0x60 0x70 0x80 0x90 0xa0 0xb0 0xc0 0xd0 0xe0 0xf0
		 * AP: 0x00 0x10 0x20 0x30 0x40 0x50 0x60 0x70 0x80 0x90 0xa0 0xb0 0xc0 0xd0 0xe0 0xf0
		 * AP/VLAN: 0x00 0x10 0x20 0x30 0x40 0x50 0x60 0x70 0x80 0x90 0xa0 0xb0 0xc0 0xd0 0xe0 0xf0
		 * mesh point: 0x00 0x10 0x20 0x30 0x40 0x50 0x60 0x70 0x80 0x90 0xa0 0xb0 0xc0 0xd0 0xe0 0xf0
		 * P2P-client: 0x00 0x10 0x20 0x30 0x40 0x50 0x60 0x70 0x80 0x90 0xa0 0xb0 0xc0 0xd0 0xe0 0xf0
		 * P2P-GO: 0x00 0x10 0x20 0x30 0x40 0x50 0x60 0x70 0x80 0x90 0xa0 0xb0 0xc0 0xd0 0xe0 0xf0
		 * P2P-device: 0x00 0x10 0x20 0x30 0x40 0x50 0x60 0x70 0x80 0x90 0xa0 0xb0 0xc0 0xd0 0xe0 0xf0
	Supported RX frame types:
		 * IBSS: 0x40 0xb0 0xc0 0xd0
		 * managed: 0x40 0xb0 0xd0
		 * AP: 0x00 0x20 0x40 0xa0 0xb0 0xc0 0xd0
		 * AP/VLAN: 0x00 0x20 0x40 0xa0 0xb0 0xc0 0xd0
		 * mesh point: 0xb0 0xc0 0xd0
		 * P2P-client: 0x40 0xd0
		 * P2P-GO: 0x00 0x20 0x40 0xa0 0xb0 0xc0 0xd0
		 * P2P-device: 0x40 0xd0
	Supported extended features:
		* [ VHT_IBSS ]: VHT-IBSS
		* [ RRM ]: RRM
		* [ FILS_STA ]: STA FILS (Fast Initial Link Setup)
		* [ CQM_RSSI_LIST ]: multiple CQM_RSSI_THOLD records
		* [ CONTROL_PORT_OVER_NL80211 ]: control port over nl80211
		* [ TXQS ]: FQ-CoDel-enabled intermediate TXQs
		* [ SCAN_RANDOM_SN ]: use random sequence numbers in scans
		* [ SCAN_MIN_PREQ_CONTENT ]: use probe request with only rate IEs in scans
		* [ AIRTIME_FAIRNESS ]: airtime fairness scheduling
		* [ AQL ]: Airtime Queue Limits (AQL)
		* [ CONTROL_PORT_NO_PREAUTH ]: disable pre-auth over nl80211 control port support
		* [ DEL_IBSS_STA ]: deletion of IBSS station support
		* [ SCAN_FREQ_KHZ ]: scan on kHz frequency support
		* [ CONTROL_PORT_OVER_NL80211_TX_STATUS ]: tx status for nl80211 control port support
		* [ POWERED_ADDR_CHANGE ]: can change MAC address while up
Wiphy phy0
	wiphy index: 0
	max # scan SSIDs: 10
	max scan IEs length: 2048 bytes
	max # sched scan SSIDs: 16
	max # match sets: 16
	Retry short limit: 7
	Retry long limit: 4
	Coverage class: 0 (up to 0m)
	Supported Ciphers:
		* WEP40 (00-0f-ac:1)
		* WEP104 (00-0f-ac:5)
		* TKIP (00-0f-ac:2)
		* CCMP-128 (00-0f-ac:4)
		* CMAC (00-0f-ac:6)
	Available Antennas: TX 0 RX 0
	Supported interface modes:
		 * IBSS
		 * managed
		 * AP
		 * P2P-client
		 * P2P-GO
		 * P2P-device
	Band 1:
		Capabilities: 0x1020
			HT20
			Static SM Power Save
			RX HT20 SGI
			No RX STBC
			Max AMSDU length: 3839 bytes
			DSSS/CCK HT40
		Maximum RX AMPDU length 65535 bytes (exponent: 0x003)
		Minimum RX AMPDU time spacing: 16 usec (0x07)
		HT TX/RX MCS rate indexes supported: 0-7
		Bitrates (non-HT):
			* 1.0 Mbps
			* 2.0 Mbps (short preamble supported)
			* 5.5 Mbps (short preamble supported)
			* 11.0 Mbps (short preamble supported)
			* 6.0 Mbps
			* 9.0 Mbps
			* 12.0 Mbps
			* 18.0 Mbps
			* 24.0 Mbps
			* 36.0 Mbps
			* 48.0 Mbps
			* 54.0 Mbps
		Frequencies:
			* 2412.0 MHz [1] (20.0 dBm)
			* 2417.0 MHz [2] (20.0 dBm)
			* 2422.0 MHz [3] (20.0 dBm)
			* 2427.0 MHz [4] (20.0 dBm)
			* 2432.0 MHz [5] (20.0 dBm)
			* 2437.0 MHz [6] (20.0 dBm)
			* 2442.0 MHz [7] (20.0 dBm)
			* 2447.0 MHz [8] (20.0 dBm)
			* 2452.0 MHz [9] (20.0 dBm)
			* 2457.0 MHz [10] (20.0 dBm)
			* 2462.0 MHz [11] (20.0 dBm)
			* 2467.0 MHz [12] (20.0 dBm)
			* 2472.0 MHz [13] (20.0 dBm)
			* 2484.0 MHz [14] (disabled)
	Band 2:
		Capabilities: 0x1062
			HT20/HT40
			Static SM Power Save
			RX HT20 SGI
			RX HT40 SGI
			No RX STBC
			Max AMSDU length: 3839 bytes
			DSSS/CCK HT40
		Maximum RX AMPDU length 65535 bytes (exponent: 0x003)
		Minimum RX AMPDU time spacing: 16 usec (0x07)
		HT TX/RX MCS rate indexes supported: 0-7
		VHT Capabilities (0x00001020):
			Max MPDU length: 3895
			Supported Channel Width: neither 160 nor 80+80
			short GI (80 MHz)
			SU Beamformee
		VHT RX MCS set:
			1 streams: MCS 0-9
			2 streams: not supported
			3 streams: not supported
			4 streams: not supported
			5 streams: not supported
			6 streams: not supported
			7 streams: not supported
			8 streams: not supported
		VHT RX highest supported: 0 Mbps
		VHT TX MCS set:
			1 streams: MCS 0-9
			2 streams: not supported
			3 streams: not supported
			4 streams: not supported
			5 streams: not supported
			6 streams: not supported
			7 streams: not supported
			8 streams: not supported
		VHT TX highest supported: 0 Mbps
		VHT extended NSS: not supported
		Bitrates (non-HT):
			* 6.0 Mbps
			* 9.0 Mbps
			* 12.0 Mbps
			* 18.0 Mbps
			* 24.0 Mbps
			* 36.0 Mbps
			* 48.0 Mbps
			* 54.0 Mbps
		Frequencies:
			* 5170.0 MHz [34] (disabled)
			* 5180.0 MHz [36] (20.0 dBm)
			* 5190.0 MHz [38] (disabled)
			* 5200.0 MHz [40] (20.0 dBm)
			* 5210.0 MHz [42] (disabled)
			* 5220.0 MHz [44] (20.0 dBm)
			* 5230.0 MHz [46] (disabled)
			* 5240.0 MHz [48] (20.0 dBm)
			* 5260.0 MHz [52] (20.0 dBm) (no IR, radar detection)
			* 5280.0 MHz [56] (20.0 dBm) (no IR, radar detection)
			* 5300.0 MHz [60] (20.0 dBm) (no IR, radar detection)
			* 5320.0 MHz [64] (20.0 dBm) (no IR, radar detection)
			* 5500.0 MHz [100] (20.0 dBm) (no IR, radar detection)
			* 5520.0 MHz [104] (20.0 dBm) (no IR, radar detection)
			* 5540.0 MHz [108] (20.0 dBm) (no IR, radar detection)
			* 5560.0 MHz [112] (20.0 dBm) (no IR, radar detection)
			* 5580.0 MHz [116] (20.0 dBm) (no IR, radar detection)
			* 5600.0 MHz [120] (20.0 dBm) (no IR, radar detection)
			* 5620.0 MHz [124] (20.0 dBm) (no IR, radar detection)
			* 5640.0 MHz [128] (20.0 dBm) (no IR, radar detection)
			* 5660.0 MHz [132] (20.0 dBm) (no IR, radar detection)
			* 5680.0 MHz [136] (20.0 dBm) (no IR, radar detection)
			* 5700.0 MHz [140] (20.0 dBm) (no IR, radar detection)
			* 5720.0 MHz [144] (disabled)
			* 5745.0 MHz [149] (disabled)
			* 5765.0 MHz [153] (disabled)
			* 5785.0 MHz [157] (disabled)
			* 5805.0 MHz [161] (disabled)
			* 5825.0 MHz [165] (disabled)
	Supported commands:
		 * new_interface
		 * set_interface
		 * new_key
		 * start_ap
...(trimmed)

### WLAN Interface: wlan1
Link + address:
wlan1            UP             10.10.0.1/24 fe80::42a5:efff:fe56:dc6a/64 

iw dev wlan1 info:
Interface wlan1
	ifindex 4
	wdev 0x100000001
	addr 40:a5:ef:56:dc:6a
	ssid ShopAP
	type AP
	wiphy 1
	channel 36 (5180 MHz), width: 20 MHz, center1: 5180 MHz
	txpower 20.00 dBm
	multicast TXQ:
		qsz-byt	qsz-pkt	flows	drops	marks	overlmt	hashcol	tx-bytes	tx-packets
		0	0	221	0	0	0	0	31250		231

iw dev wlan1 link:
Not connected.

iwconfig wlan1:
wlan1     IEEE 802.11  Mode:Master  Tx-Power=20 dBm   
          Retry short limit:7   RTS thr:off   Fragment thr:off
          Power Management:off
          


### WLAN Interface: wlan0
Link + address:
wlan0            DOWN           

iw dev wlan0 info:
Interface wlan0
	ifindex 3
	wdev 0x1
	addr b8:27:eb:51:c9:c0
	type managed
	wiphy 0
	channel 34 (5170 MHz), width: 20 MHz, center1: 5170 MHz

iw dev wlan0 link:
Not connected.

iwconfig wlan0:
wlan0     IEEE 802.11  ESSID:off/any  
          Mode:Managed  Access Point: Not-Associated   
          Retry short limit:7   RTS thr:off   Fragment thr:off
          Encryption key:off
          Power Management:on
          



**Routing & Policy**
Routes (all tables):
default via 10.0.0.1 dev eth0 proto dhcp src 10.0.0.64 metric 100 
10.0.0.0/24 dev eth0 proto kernel scope link src 10.0.0.64 metric 100 
10.10.0.0/24 dev wlan1 proto kernel scope link src 10.10.0.1 metric 600 
local 10.0.0.64 dev eth0 table local proto kernel scope host src 10.0.0.64 
broadcast 10.0.0.255 dev eth0 table local proto kernel scope link src 10.0.0.64 
local 10.10.0.1 dev wlan1 table local proto kernel scope host src 10.10.0.1 
broadcast 10.10.0.255 dev wlan1 table local proto kernel scope link src 10.10.0.1 
local 127.0.0.0/8 dev lo table local proto kernel scope host src 127.0.0.1 
local 127.0.0.1 dev lo table local proto kernel scope host src 127.0.0.1 
broadcast 127.255.255.255 dev lo table local proto kernel scope link src 127.0.0.1 
fe80::/64 dev wlan1 proto kernel metric 256 pref medium
fe80::/64 dev eth0 proto kernel metric 1024 pref medium
local ::1 dev lo table local proto kernel metric 0 pref medium
local fe80::1c9b:bcef:9ef9:98d dev eth0 table local proto kernel metric 0 pref medium
local fe80::42a5:efff:fe56:dc6a dev wlan1 table local proto kernel metric 0 pref medium
multicast ff00::/8 dev eth0 table local proto kernel metric 256 pref medium
multicast ff00::/8 dev wlan1 table local proto kernel metric 256 pref medium

Rules:
0:	from all lookup local
32766:	from all lookup main
32767:	from all lookup default

**Listeners (TCP/UDP)**
TCP:
State  Recv-Q Send-Q Local Address:Port Peer Address:PortProcess                                                                                                                              
LISTEN 0      4096       127.0.0.1:631       0.0.0.0:*    users:(("cupsd",pid=1958,fd=8))                                                                                                     
LISTEN 0      4096         0.0.0.0:111       0.0.0.0:*    users:(("rpcbind",pid=498,fd=4),("systemd",pid=1,fd=97))                                                                            
LISTEN 0      511          0.0.0.0:80        0.0.0.0:*    users:(("nginx",pid=4312,fd=6),("nginx",pid=4311,fd=6),("nginx",pid=4310,fd=6),("nginx",pid=4309,fd=6),("nginx",pid=1385,fd=6))     
LISTEN 0      128          0.0.0.0:22        0.0.0.0:*    users:(("sshd",pid=1024,fd=6))                                                                                                      
LISTEN 0      511          0.0.0.0:443       0.0.0.0:*    users:(("nginx",pid=4312,fd=5),("nginx",pid=4311,fd=5),("nginx",pid=4310,fd=5),("nginx",pid=4309,fd=5),("nginx",pid=1385,fd=5))     
LISTEN 0      128          0.0.0.0:5000      0.0.0.0:*    users:(("api_server",pid=1008,fd=6))                                                                                                
LISTEN 0      32         10.10.0.1:53        0.0.0.0:*    users:(("dnsmasq",pid=1341,fd=7))                                                                                                   
LISTEN 0      4096           [::1]:631          [::]:*    users:(("cupsd",pid=1958,fd=7))                                                                                                     
LISTEN 0      4096            [::]:111          [::]:*    users:(("rpcbind",pid=498,fd=6),("systemd",pid=1,fd=99))                                                                            
LISTEN 0      511             [::]:80           [::]:*    users:(("nginx",pid=4312,fd=17),("nginx",pid=4311,fd=17),("nginx",pid=4310,fd=17),("nginx",pid=4309,fd=17),("nginx",pid=1385,fd=17))
LISTEN 0      128             [::]:22           [::]:*    users:(("sshd",pid=1024,fd=7))                                                                                                      

UDP:
State  Recv-Q Send-Q Local Address:Port  Peer Address:PortProcess                                                   
UNCONN 0      832        10.10.0.1:53         0.0.0.0:*    users:(("dnsmasq",pid=1341,fd=6))                        
UNCONN 0      0            0.0.0.0:67         0.0.0.0:*    users:(("dnsmasq",pid=1341,fd=4))                        
UNCONN 0      0            0.0.0.0:111        0.0.0.0:*    users:(("rpcbind",pid=498,fd=5),("systemd",pid=1,fd=98)) 
UNCONN 0      0            0.0.0.0:36007      0.0.0.0:*    users:(("avahi-daemon",pid=612,fd=14))                   
UNCONN 0      0            0.0.0.0:5353       0.0.0.0:*    users:(("avahi-daemon",pid=612,fd=12))                   
UNCONN 0      0                  *:58472            *:*    users:(("avahi-daemon",pid=612,fd=15))                   
UNCONN 0      0                  *:111              *:*    users:(("rpcbind",pid=498,fd=7),("systemd",pid=1,fd=100))
UNCONN 0      0                  *:5353             *:*    users:(("avahi-daemon",pid=612,fd=13))                   

**Firewall / NAT**
iptables (filter):
iptables not present

iptables (nat):

nftables ruleset:

sysctl forwarding:
net.ipv4.ip_forward = 1


**Services (enabled)**
UNIT FILE                          STATE   PRESET
cups.path                          enabled enabled
accounts-daemon.service            enabled enabled
api_server.service                 enabled enabled
apparmor.service                   enabled enabled
avahi-daemon.service               enabled enabled
bluetooth.service                  enabled enabled
cloud-config.service               enabled enabled
cloud-final.service                enabled enabled
cloud-init-local.service           enabled enabled
cloud-init-main.service            enabled enabled
cloud-init-network.service         enabled enabled
console-setup.service              enabled enabled
cron.service                       enabled enabled
cups-browsed.service               enabled enabled
cups.service                       enabled enabled
e2scrub_reap.service               enabled enabled
getty@.service                     enabled enabled
glamor-test.service                enabled enabled
keyboard-setup.service             enabled enabled
lightdm.service                    enabled enabled
ModemManager.service               enabled enabled
NetworkManager-dispatcher.service  enabled enabled
NetworkManager-wait-online.service enabled enabled
NetworkManager.service             enabled enabled
nfs-blkmap.service                 enabled enabled
nginx.service                      enabled enabled
regenerate_ssh_host_keys.service   enabled enabled
rp1-test.service                   enabled enabled
rpcbind.service                    enabled enabled
rpi-eeprom-update.service          enabled enabled
rtc-init.service                   enabled enabled
scanner_listener.service           enabled enabled
ssh.service                        enabled enabled
sshd-keygen.service                enabled enabled
sshswitch.service                  enabled enabled
systemd-pstore.service             enabled enabled
systemd-timesyncd.service          enabled enabled
udisks2.service                    enabled enabled
wayvnc-control.service             enabled enabled
wpa_supplicant.service             enabled enabled
avahi-daemon.socket                enabled enabled
cloud-init-hotplugd.socket         enabled enabled
cups.socket                        enabled enabled
rpcbind.socket                     enabled enabled
nfs-client.target                  enabled enabled
remote-fs.target                   enabled enabled
apt-daily-upgrade.timer            enabled enabled
apt-daily.timer                    enabled enabled
dpkg-db-backup.timer               enabled enabled
e2scrub_all.timer                  enabled enabled
fstrim.timer                       enabled enabled
logrotate.timer                    enabled enabled
man-db.timer                       enabled enabled

53 unit files listed.


**Services (running)**
  UNIT                       LOAD   ACTIVE SUB     DESCRIPTION
  accounts-daemon.service    loaded active running Accounts Service
  api_server.service         loaded active running Packet Shop API Server (dist binary)
  avahi-daemon.service       loaded active running Avahi mDNS/DNS-SD Stack
  bluetooth.service          loaded active running Bluetooth service
  colord.service             loaded active running Manage, Install and Generate Color Profiles
  cron.service               loaded active running Regular background program processing daemon
  cups-browsed.service       loaded active running Make remote CUPS printers available locally
  cups.service               loaded active running CUPS Scheduler
  dbus.service               loaded active running D-Bus System Message Bus
  getty@tty1.service         loaded active running Getty on tty1
  lightdm.service            loaded active running Light Display Manager
  ModemManager.service       loaded active running Modem Manager
  NetworkManager.service     loaded active running Network Manager
  nfs-blkmap.service         loaded active running pNFS block layout mapping daemon
  nginx.service              loaded active running A high performance web server and a reverse proxy server
  polkit.service             loaded active running Authorization Manager
  rpcbind.service            loaded active running RPC bind portmap service
  scanner_listener.service   loaded active running Packet Shop Scanner Listener (dist binary)
  serial-getty@ttyS0.service loaded active running Serial Getty on ttyS0
  ssh.service                loaded active running OpenBSD Secure Shell server
  systemd-hostnamed.service  loaded active running Hostname Service
  systemd-journald.service   loaded active running Journal Service
  systemd-logind.service     loaded active running User Login Management
  systemd-timesyncd.service  loaded active running Network Time Synchronization
  systemd-udevd.service      loaded active running Rule-based Manager for Device Events and Files
  udisks2.service            loaded active running Disk Manager
  user@1000.service          loaded active running User Manager for UID 1000
  wpa_supplicant.service     loaded active running WPA supplicant

Legend: LOAD   → Reflects whether the unit definition was properly loaded.
        ACTIVE → The high-level unit activation state, i.e. generalization of SUB.
        SUB    → The low-level unit activation state, values depend on unit type.

28 loaded units listed.


**Key Service Status**
== nginx ==
enabled
active
● nginx.service - A high performance web server and a reverse proxy server
     Loaded: loaded (/usr/lib/systemd/system/nginx.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/nginx.service.d
             └─override.conf
     Active: active (running) since Wed 2026-01-28 22:13:11 CET; 10h ago
 Invocation: fc55280c9a3441378408381be2caebc9
       Docs: man:nginx(8)
   Main PID: 1385 (nginx)
      Tasks: 5 (limit: 1555)
        CPU: 3.009s
     CGroup: /system.slice/nginx.service
             ├─1385 "nginx: master process /usr/sbin/nginx -g daemon on; master_process on;"
             ├─4309 "nginx: worker process"
             ├─4310 "nginx: worker process"
             ├─4311 "nginx: worker process"
             └─4312 "nginx: worker process"

Jan 28 22:13:10 packetshop systemd[1]: Starting nginx.service - A high performance web server and a reverse proxy server...
Jan 28 22:13:11 packetshop systemd[1]: Started nginx.service - A high performance web server and a reverse proxy server.
Jan 29 08:39:59 packetshop systemd[1]: Reloading nginx.service - A high performance web server and a reverse proxy server...
Jan 29 08:40:00 packetshop nginx[4307]: 2026/01/29 08:39:59 [notice] 4307#4307: signal process started
Jan 29 08:40:00 packetshop systemd[1]: Reloaded nginx.service - A high performance web server and a reverse proxy server.

== apache2 ==
not-found
failed
× apache2.service
     Loaded: not-found (Reason: Unit apache2.service not found.)
     Active: failed (Result: exit-code) since Thu 2026-01-29 08:33:59 CET; 17min ago
 Invocation: 97cb86454e094eefbeb180aca8df1990
        CPU: 162ms

Jan 29 08:33:59 packetshop systemd[1]: Starting apache2.service - The Apache HTTP Server...
Jan 29 08:33:59 packetshop apachectl[4192]: (98)Address already in use: AH00072: make_sock: could not bind to address [::]:80
Jan 29 08:33:59 packetshop apachectl[4192]: (98)Address already in use: AH00072: make_sock: could not bind to address [::]:80
Jan 29 08:33:59 packetshop apachectl[4192]: (98)Address already in use: AH00072: make_sock: could not bind to address 0.0.0.0:80
Jan 29 08:33:59 packetshop apachectl[4192]: no listening sockets available, shutting down
Jan 29 08:33:59 packetshop apachectl[4192]: AH00015: Unable to open logs
Jan 29 08:33:59 packetshop systemd[1]: apache2.service: Control process exited, code=exited, status=1/FAILURE
Jan 29 08:33:59 packetshop systemd[1]: apache2.service: Failed with result 'exit-code'.
Jan 29 08:33:59 packetshop systemd[1]: Failed to start apache2.service - The Apache HTTP Server.
Jan 29 08:35:02 packetshop systemd[1]: apache2.service: Unit cannot be reloaded because it is inactive.

== dnsmasq ==
not-found
inactive

== hostapd ==
not-found
inactive


**APT / Packages**
Sources:
Types: deb
URIs: http://raspbian.raspberrypi.com/raspbian/
Architectures: armhf
Suites: trixie
Components: main contrib non-free rpi
Signed-By: /usr/share/keyrings/raspbian-archive-keyring.gpg
Types: deb
URIs: http://archive.raspberrypi.com/debian/
Suites: trixie
Components: main
Signed-By: /usr/share/keyrings/raspberrypi-archive-keyring.pgp

Manual packages (apt-mark showmanual):
adduser
apt
apt-listchanges
apt-utils
avahi-daemon
base-files
base-passwd
bash
bash-completion
bluez
bluez-firmware
bsdextrautils
bsdutils
build-essential
ca-certificates
cifs-utils
cloud-init
console-setup
coreutils
cpio
cpufrequtils
cron
cron-daemon-common
cups
cups-client
curl
dash
debconf
debconf-i18n
debconf-utils
debianutils
dhcpcd-base
diffutils
dirmngr
dmidecode
dosfstools
dpkg
e2fsprogs
ed
ethtool
evtest
fbset
fdisk
file
findutils
firmware-atheros
firmware-brcm80211
firmware-libertas
firmware-mediatek
firmware-misc-nonfree
firmware-realtek
gcc-10-base
gcc-14-base
gcc-7-base
gcc-8-base
gcc-9-base
gdb
gnupg
gnupg-l10n
gpg
gpg-agent
gpgconf
gpgsm
gpgv
gpiod
grep
groff-base
gzip
hostname
htop
i2c-tools
init
initramfs-tools
init-system-helpers
install-info
iproute2
iputils-ping
isc-dhcp-client
isc-dhcp-common
keyboard-configuration
kmod
kms++-utils
less
libacl1
libapparmor1
libapt-pkg7.0
libassuan9
libatomic1
libattr1
libaudit1
libaudit-common
libblkid1
libbpf1
libbsd0
libbz2-1.0
libc6
libcap2
libcap2-bin
libcap-ng0
libc-bin
libcom-err2
libcrypt1
libdb5.3t64
libdebconfclient0
libedit2
libelf1t64
libext2fs2t64
libfdisk1
libffi8
libffi-dev
libgcc-s1
libgcrypt20
libgdbm6t64
libgmp10
libgnutls30t64
libgpg-error0
libgssapi-krb5-2
libhogweed6t64
libidn2-0
libjansson4
libk5crypto3
libkeyutils1
libkmod2
libkrb5-3
libkrb5support0
libksba8
liblastlog2-2
libldap2
liblocale-gettext-perl
liblz4-1
liblzma5
libmd0
libmnl0
libmount1
libmtp-runtime
libncursesw6
libnettle8t64
libnftables1
libnftnl11
libnpth0t64
libp11-kit0
libpam0g
libpam-chksshpwd
libpam-modules
libpam-modules-bin
libpam-runtime
libpcre2-8-0
libpipeline1
libpopt0
libproc2-0
libreadline8t64
libsasl2-2
libsasl2-modules-db
libseccomp2
libselinux1
libsemanage2
libsemanage-common
libsepol2
libsigc++-1.2-5c2
libsmartcols1
libsqlite3-0
libss2
libssl3t64
libstdc++6
libsystemd0
libsystemd-shared
libtasn1-6
libtext-charwidth-perl
libtext-iconv-perl
libtext-wrapi18n-perl
libtinfo6
libtirpc3t64
libtirpc-common
libuchardet0
libudev1
libunistring5
libuuid1
libxtables12
libxxhash0
libzstd1
linux-headers-rpi-v6
linux-headers-rpi-v7
linux-image-rpi-v6
linux-image-rpi-v7
linux-image-rpi-v8:arm64
linux-sysctl-defaults
locales
login
login.defs
logrotate
logsave
lsb-base
lua5.1
luajit
man-db
manpages-dev
mawk
mkvtoolnix
mount
nano
ncdu
ncurses-base
ncurses-bin
netbase
netcat-openbsd
net-tools
network-manager
nftables
nginx
ntfs-3g
openssl
openssl-provider-legacy
p7zip-full
parted
passwd
paxctld
pciutils
perl-base
pinentry-curses
pkg-config
procps
psmisc
python3-dev
python3-evdev
python3-full
python3-gpiozero
python3-libgpiod
python3-rpi-lgpio
python3-smbus2
python3-spidev
python3-venv
python-is-python3
raspberrypi-archive-keyring
raspberrypi-net-mods
raspberrypi-sys-mods
raspbian-archive-keyring
raspi-config
raspi-copies-and-fills
raspi-firmware
raspi-utils
readline-common
rpd-applications
rpd-developer
rpd-graphics
rpd-preferences
rpd-theme
rpd-utilities
rpd-wayland-core
rpd-wayland-extras
rpd-x-core
rpd-x-extras
rpicam-apps-lite
rpi-cloud-init-mods
rpi-eeprom
rpi-keyboard-config
rpi-keyboard-fw-update
rpi-loop-utils
rpi-swap
rpi-update
rpi-usb-gadget
rsync
sed
sensible-utils
sqv
ssh
ssh-import-id
strace
sudo
systemd
systemd-sysv
systemd-timesyncd
sysvinit-utils
tar
traceroute
tzdata
udev
udisks2
unzip
usb-modeswitch
usbutils
userconf-pi
util-linux
v4l-utils
vim-common
vim-tiny
wireless-tools
wpasupplicant
zip
zlib1g

Recent APT history:

Start-Date: 2026-01-11  22:24:10
Commandline: apt install -y python3-venv python3-full
Requested-By: admin (1000)
Install: idle-python3.13:armhf (3.13.5-2, automatic), python3-full:armhf (3.13.5-1), python3-gdbm:armhf (3.13.5-1, automatic), libpython3.13-testsuite:armhf (3.13.5-2, automatic), python3.13-full:armhf (3.13.5-2, automatic), python3-doc:armhf (3.13.5-1, automatic), python3-examples:armhf (3.13.5-1, automatic), fonts-mathjax:armhf (2.7.9+dfsg-1, automatic), libjs-mathjax:armhf (2.7.9+dfsg-1, automatic), python3.13-gdbm:armhf (3.13.5-2, automatic), python3.13-doc:armhf (3.13.5-2, automatic), idle:armhf (3.13.5-1, automatic), python3.13-examples:armhf (3.13.5-2, automatic)
End-Date: 2026-01-11  22:25:10

Start-Date: 2026-01-12  09:17:04
Commandline: apt install -y libffi-dev python3-dev build-essential pkg-config
Requested-By: admin (1000)
Install: libffi-dev:armhf (3.4.8-2)
End-Date: 2026-01-12  09:17:10

Start-Date: 2026-01-21  17:21:33
Commandline: apt install -y cups cups-client python3-evdev
Requested-By: admin (1000)
Install: python3-evdev:armhf (1.9.1-1)
End-Date: 2026-01-21  17:21:36

Start-Date: 2026-01-22  09:21:55
Commandline: apt-get install -y evtest
Requested-By: admin (1000)
Install: evtest:armhf (1:1.35-1), libevemu3t64:armhf (2.7.0-4, automatic), evemu-tools:armhf (2.7.0-4, automatic)
End-Date: 2026-01-22  09:22:04

Start-Date: 2026-01-22  17:00:15
Commandline: apt install -y firmware-misc-nonfree
Requested-By: admin (1000)
Install: firmware-nvidia-graphics:armhf (1:20241210-1+rpt4, automatic), firmware-misc-nonfree:armhf (1:20241210-1+rpt4), firmware-intel-misc:armhf (1:20241210-1+rpt4, automatic), firmware-intel-graphics:armhf (1:20241210-1+rpt4, automatic)
End-Date: 2026-01-22  17:03:09

Start-Date: 2026-01-23  15:36:39
Commandline: apt install -y nginx openssl
Requested-By: admin (1000)
Install: nginx:armhf (1.26.3-3+deb13u1), nginx-common:armhf (1.26.3-3+deb13u1, automatic)
End-Date: 2026-01-23  15:37:01

Start-Date: 2026-01-24  23:46:16
Commandline: apt install -y cpufrequtils
Requested-By: admin (1000)
Install: libcpufreq0:armhf (008-2, automatic), cpufrequtils:armhf (008-2)
End-Date: 2026-01-24  23:46:39

Start-Date: 2026-01-29  08:25:01
Commandline: apt-get install -y apache2 curl
Requested-By: admin (1000)
Install: libaprutil1t64:armhf (1.6.3-3+b1, automatic), libaprutil1-dbd-sqlite3:armhf (1.6.3-3+b1, automatic), apache2-data:armhf (2.4.66-1~deb13u1, automatic), apache2-bin:armhf (2.4.66-1~deb13u1, automatic), apache2-utils:armhf (2.4.66-1~deb13u1, automatic), apache2:armhf (2.4.66-1~deb13u1), libaprutil1-ldap:armhf (1.6.3-3+b1, automatic), libapr1t64:armhf (1.7.5-1, automatic)
End-Date: 2026-01-29  08:26:00

Start-Date: 2026-01-29  08:44:02
Commandline: apt-get purge -y apache2 apache2-bin apache2-data apache2-utils
Requested-By: admin (1000)
Purge: apache2-data:armhf (2.4.66-1~deb13u1), apache2-bin:armhf (2.4.66-1~deb13u1), apache2-utils:armhf (2.4.66-1~deb13u1), apache2:armhf (2.4.66-1~deb13u1)
End-Date: 2026-01-29  08:44:37

Recent dpkg log:
2026-01-22 09:21:57 install evtest:armhf <none> 1:1.35-1
2026-01-22 09:21:57 status half-installed evtest:armhf 1:1.35-1
2026-01-22 09:21:57 status unpacked evtest:armhf 1:1.35-1
2026-01-22 09:21:58 startup packages configure
2026-01-22 09:21:58 configure libevemu3t64:armhf 2.7.0-4 <none>
2026-01-22 09:21:58 status unpacked libevemu3t64:armhf 2.7.0-4
2026-01-22 09:21:58 status half-configured libevemu3t64:armhf 2.7.0-4
2026-01-22 09:21:58 status installed libevemu3t64:armhf 2.7.0-4
2026-01-22 09:21:58 configure evtest:armhf 1:1.35-1 <none>
2026-01-22 09:21:58 status unpacked evtest:armhf 1:1.35-1
2026-01-22 09:21:58 status half-configured evtest:armhf 1:1.35-1
2026-01-22 09:21:58 status installed evtest:armhf 1:1.35-1
2026-01-22 09:21:58 configure evemu-tools:armhf 2.7.0-4 <none>
2026-01-22 09:21:58 status unpacked evemu-tools:armhf 2.7.0-4
2026-01-22 09:21:58 status half-configured evemu-tools:armhf 2.7.0-4
2026-01-22 09:21:58 status installed evemu-tools:armhf 2.7.0-4
2026-01-22 09:21:58 trigproc man-db:armhf 2.13.1-1 <none>
2026-01-22 09:21:58 status half-configured man-db:armhf 2.13.1-1
2026-01-22 09:22:03 status installed man-db:armhf 2.13.1-1
2026-01-22 09:22:03 trigproc libc-bin:armhf 2.41-12+rpt1 <none>
2026-01-22 09:22:03 status half-configured libc-bin:armhf 2.41-12+rpt1
2026-01-22 09:22:03 status installed libc-bin:armhf 2.41-12+rpt1
2026-01-22 17:00:15 startup archives unpack
2026-01-22 17:00:16 install firmware-intel-graphics:all <none> 1:20241210-1+rpt4
2026-01-22 17:00:16 status half-installed firmware-intel-graphics:all 1:20241210-1+rpt4
2026-01-22 17:00:23 status unpacked firmware-intel-graphics:all 1:20241210-1+rpt4
2026-01-22 17:00:23 install firmware-intel-misc:all <none> 1:20241210-1+rpt4
2026-01-22 17:00:23 status half-installed firmware-intel-misc:all 1:20241210-1+rpt4
2026-01-22 17:00:25 status unpacked firmware-intel-misc:all 1:20241210-1+rpt4
2026-01-22 17:00:25 install firmware-misc-nonfree:all <none> 1:20241210-1+rpt4
2026-01-22 17:00:25 status half-installed firmware-misc-nonfree:all 1:20241210-1+rpt4
2026-01-22 17:00:27 status unpacked firmware-misc-nonfree:all 1:20241210-1+rpt4
2026-01-22 17:00:27 install firmware-nvidia-graphics:all <none> 1:20241210-1+rpt4
2026-01-22 17:00:27 status half-installed firmware-nvidia-graphics:all 1:20241210-1+rpt4
2026-01-22 17:01:08 status unpacked firmware-nvidia-graphics:all 1:20241210-1+rpt4
2026-01-22 17:01:09 startup packages configure
2026-01-22 17:01:09 configure firmware-intel-graphics:all 1:20241210-1+rpt4 <none>
2026-01-22 17:01:09 status unpacked firmware-intel-graphics:all 1:20241210-1+rpt4
2026-01-22 17:01:09 status half-configured firmware-intel-graphics:all 1:20241210-1+rpt4
2026-01-22 17:01:14 status installed firmware-intel-graphics:all 1:20241210-1+rpt4
2026-01-22 17:01:14 configure firmware-misc-nonfree:all 1:20241210-1+rpt4 <none>
2026-01-22 17:01:14 status unpacked firmware-misc-nonfree:all 1:20241210-1+rpt4
2026-01-22 17:01:14 status half-configured firmware-misc-nonfree:all 1:20241210-1+rpt4
2026-01-22 17:01:14 status installed firmware-misc-nonfree:all 1:20241210-1+rpt4
2026-01-22 17:01:14 status triggers-pending initramfs-tools:all 0.148.3+rpt2
2026-01-22 17:01:14 configure firmware-nvidia-graphics:all 1:20241210-1+rpt4 <none>
2026-01-22 17:01:14 status unpacked firmware-nvidia-graphics:all 1:20241210-1+rpt4
2026-01-22 17:01:14 status half-configured firmware-nvidia-graphics:all 1:20241210-1+rpt4
2026-01-22 17:01:49 status installed firmware-nvidia-graphics:all 1:20241210-1+rpt4
2026-01-22 17:01:49 configure firmware-intel-misc:all 1:20241210-1+rpt4 <none>
2026-01-22 17:01:49 status unpacked firmware-intel-misc:all 1:20241210-1+rpt4
2026-01-22 17:01:49 status half-configured firmware-intel-misc:all 1:20241210-1+rpt4
2026-01-22 17:01:50 status installed firmware-intel-misc:all 1:20241210-1+rpt4
2026-01-22 17:01:50 trigproc initramfs-tools:all 0.148.3+rpt2 <none>
2026-01-22 17:01:50 status half-configured initramfs-tools:all 0.148.3+rpt2
2026-01-22 17:03:09 status installed initramfs-tools:all 0.148.3+rpt2
2026-01-23 15:36:39 startup archives unpack
2026-01-23 15:36:41 install nginx-common:all <none> 1.26.3-3+deb13u1
2026-01-23 15:36:41 status half-installed nginx-common:all 1.26.3-3+deb13u1
2026-01-23 15:36:41 status unpacked nginx-common:all 1.26.3-3+deb13u1
2026-01-23 15:36:42 install nginx:armhf <none> 1.26.3-3+deb13u1
2026-01-23 15:36:42 status half-installed nginx:armhf 1.26.3-3+deb13u1
2026-01-23 15:36:42 status triggers-pending man-db:armhf 2.13.1-1
2026-01-23 15:36:42 status unpacked nginx:armhf 1.26.3-3+deb13u1
2026-01-23 15:36:42 startup packages configure
2026-01-23 15:36:43 configure nginx-common:all 1.26.3-3+deb13u1 <none>
2026-01-23 15:36:43 status unpacked nginx-common:all 1.26.3-3+deb13u1
2026-01-23 15:36:43 status half-configured nginx-common:all 1.26.3-3+deb13u1
2026-01-23 15:36:56 status installed nginx-common:all 1.26.3-3+deb13u1
2026-01-23 15:36:56 configure nginx:armhf 1.26.3-3+deb13u1 <none>
2026-01-23 15:36:56 status unpacked nginx:armhf 1.26.3-3+deb13u1
2026-01-23 15:36:56 status half-configured nginx:armhf 1.26.3-3+deb13u1
2026-01-23 15:36:58 status installed nginx:armhf 1.26.3-3+deb13u1
2026-01-23 15:36:58 trigproc man-db:armhf 2.13.1-1 <none>
2026-01-23 15:36:58 status half-configured man-db:armhf 2.13.1-1
2026-01-23 15:37:00 status installed man-db:armhf 2.13.1-1
2026-01-24 23:46:16 startup archives unpack
2026-01-24 23:46:18 install libcpufreq0:armhf <none> 008-2
2026-01-24 23:46:18 status triggers-pending libc-bin:armhf 2.41-12+rpt1
2026-01-24 23:46:18 status half-installed libcpufreq0:armhf 008-2
2026-01-24 23:46:18 status unpacked libcpufreq0:armhf 008-2
2026-01-24 23:46:18 install cpufrequtils:armhf <none> 008-2
2026-01-24 23:46:18 status half-installed cpufrequtils:armhf 008-2
2026-01-24 23:46:19 status triggers-pending man-db:armhf 2.13.1-1
2026-01-24 23:46:19 status unpacked cpufrequtils:armhf 008-2
2026-01-24 23:46:19 startup packages configure
2026-01-24 23:46:19 configure libcpufreq0:armhf 008-2 <none>
2026-01-24 23:46:19 status unpacked libcpufreq0:armhf 008-2
2026-01-24 23:46:19 status half-configured libcpufreq0:armhf 008-2
2026-01-24 23:46:19 status installed libcpufreq0:armhf 008-2
2026-01-24 23:46:19 configure cpufrequtils:armhf 008-2 <none>
2026-01-24 23:46:19 status unpacked cpufrequtils:armhf 008-2
2026-01-24 23:46:19 status half-configured cpufrequtils:armhf 008-2
2026-01-24 23:46:31 status installed cpufrequtils:armhf 008-2
2026-01-24 23:46:31 trigproc man-db:armhf 2.13.1-1 <none>
2026-01-24 23:46:31 status half-configured man-db:armhf 2.13.1-1
2026-01-24 23:46:38 status installed man-db:armhf 2.13.1-1
2026-01-24 23:46:38 trigproc libc-bin:armhf 2.41-12+rpt1 <none>
2026-01-24 23:46:38 status half-configured libc-bin:armhf 2.41-12+rpt1
2026-01-24 23:46:39 status installed libc-bin:armhf 2.41-12+rpt1
2026-01-29 08:25:01 startup archives unpack
2026-01-29 08:25:03 install libapr1t64:armhf <none> 1.7.5-1
2026-01-29 08:25:03 status triggers-pending libc-bin:armhf 2.41-12+rpt1
2026-01-29 08:25:03 status half-installed libapr1t64:armhf 1.7.5-1
2026-01-29 08:25:03 status unpacked libapr1t64:armhf 1.7.5-1
2026-01-29 08:25:03 install libaprutil1t64:armhf <none> 1.6.3-3+b1
2026-01-29 08:25:03 status half-installed libaprutil1t64:armhf 1.6.3-3+b1
2026-01-29 08:25:04 status unpacked libaprutil1t64:armhf 1.6.3-3+b1
2026-01-29 08:25:04 install libaprutil1-dbd-sqlite3:armhf <none> 1.6.3-3+b1
2026-01-29 08:25:04 status half-installed libaprutil1-dbd-sqlite3:armhf 1.6.3-3+b1
2026-01-29 08:25:04 status unpacked libaprutil1-dbd-sqlite3:armhf 1.6.3-3+b1
2026-01-29 08:25:04 install libaprutil1-ldap:armhf <none> 1.6.3-3+b1
2026-01-29 08:25:04 status half-installed libaprutil1-ldap:armhf 1.6.3-3+b1
2026-01-29 08:25:04 status unpacked libaprutil1-ldap:armhf 1.6.3-3+b1
2026-01-29 08:25:04 install apache2-bin:armhf <none> 2.4.66-1~deb13u1
2026-01-29 08:25:04 status half-installed apache2-bin:armhf 2.4.66-1~deb13u1
2026-01-29 08:25:05 status triggers-pending man-db:armhf 2.13.1-1
2026-01-29 08:25:05 status unpacked apache2-bin:armhf 2.4.66-1~deb13u1
2026-01-29 08:25:06 install apache2-data:all <none> 2.4.66-1~deb13u1
2026-01-29 08:25:06 status half-installed apache2-data:all 2.4.66-1~deb13u1
2026-01-29 08:25:06 status unpacked apache2-data:all 2.4.66-1~deb13u1
2026-01-29 08:25:06 install apache2-utils:armhf <none> 2.4.66-1~deb13u1
2026-01-29 08:25:06 status half-installed apache2-utils:armhf 2.4.66-1~deb13u1
2026-01-29 08:25:06 status unpacked apache2-utils:armhf 2.4.66-1~deb13u1
2026-01-29 08:25:07 install apache2:armhf <none> 2.4.66-1~deb13u1
2026-01-29 08:25:07 status half-installed apache2:armhf 2.4.66-1~deb13u1
2026-01-29 08:25:07 status unpacked apache2:armhf 2.4.66-1~deb13u1
2026-01-29 08:25:08 startup packages configure
2026-01-29 08:25:08 configure libapr1t64:armhf 1.7.5-1 <none>
2026-01-29 08:25:08 status unpacked libapr1t64:armhf 1.7.5-1
2026-01-29 08:25:08 status half-configured libapr1t64:armhf 1.7.5-1
2026-01-29 08:25:08 status installed libapr1t64:armhf 1.7.5-1
2026-01-29 08:25:08 configure apache2-data:all 2.4.66-1~deb13u1 <none>
2026-01-29 08:25:08 status unpacked apache2-data:all 2.4.66-1~deb13u1
2026-01-29 08:25:08 status half-configured apache2-data:all 2.4.66-1~deb13u1
2026-01-29 08:25:08 status installed apache2-data:all 2.4.66-1~deb13u1
2026-01-29 08:25:08 configure libaprutil1t64:armhf 1.6.3-3+b1 <none>
2026-01-29 08:25:08 status unpacked libaprutil1t64:armhf 1.6.3-3+b1
2026-01-29 08:25:08 status half-configured libaprutil1t64:armhf 1.6.3-3+b1
2026-01-29 08:25:08 status installed libaprutil1t64:armhf 1.6.3-3+b1
2026-01-29 08:25:08 configure libaprutil1-ldap:armhf 1.6.3-3+b1 <none>
2026-01-29 08:25:08 status unpacked libaprutil1-ldap:armhf 1.6.3-3+b1
2026-01-29 08:25:08 status half-configured libaprutil1-ldap:armhf 1.6.3-3+b1
2026-01-29 08:25:08 status installed libaprutil1-ldap:armhf 1.6.3-3+b1
2026-01-29 08:25:08 configure libaprutil1-dbd-sqlite3:armhf 1.6.3-3+b1 <none>
2026-01-29 08:25:08 status unpacked libaprutil1-dbd-sqlite3:armhf 1.6.3-3+b1
2026-01-29 08:25:08 status half-configured libaprutil1-dbd-sqlite3:armhf 1.6.3-3+b1
2026-01-29 08:25:08 status installed libaprutil1-dbd-sqlite3:armhf 1.6.3-3+b1
2026-01-29 08:25:08 configure apache2-utils:armhf 2.4.66-1~deb13u1 <none>
2026-01-29 08:25:08 status unpacked apache2-utils:armhf 2.4.66-1~deb13u1
2026-01-29 08:25:08 status half-configured apache2-utils:armhf 2.4.66-1~deb13u1
2026-01-29 08:25:08 status installed apache2-utils:armhf 2.4.66-1~deb13u1
2026-01-29 08:25:08 configure apache2-bin:armhf 2.4.66-1~deb13u1 <none>
2026-01-29 08:25:08 status unpacked apache2-bin:armhf 2.4.66-1~deb13u1
2026-01-29 08:25:08 status half-configured apache2-bin:armhf 2.4.66-1~deb13u1
2026-01-29 08:25:08 status installed apache2-bin:armhf 2.4.66-1~deb13u1
2026-01-29 08:25:08 configure apache2:armhf 2.4.66-1~deb13u1 <none>
2026-01-29 08:25:08 status unpacked apache2:armhf 2.4.66-1~deb13u1
2026-01-29 08:25:10 status half-configured apache2:armhf 2.4.66-1~deb13u1
2026-01-29 08:25:51 status installed apache2:armhf 2.4.66-1~deb13u1
2026-01-29 08:25:51 trigproc man-db:armhf 2.13.1-1 <none>
2026-01-29 08:25:51 status half-configured man-db:armhf 2.13.1-1
2026-01-29 08:25:59 status installed man-db:armhf 2.13.1-1
2026-01-29 08:25:59 trigproc libc-bin:armhf 2.41-12+rpt1 <none>
2026-01-29 08:25:59 status half-configured libc-bin:armhf 2.41-12+rpt1
2026-01-29 08:26:00 status installed libc-bin:armhf 2.41-12+rpt1
2026-01-29 08:44:02 startup packages remove
2026-01-29 08:44:02 status installed apache2:armhf 2.4.66-1~deb13u1
2026-01-29 08:44:03 remove apache2:armhf 2.4.66-1~deb13u1 <none>
2026-01-29 08:44:03 status half-configured apache2:armhf 2.4.66-1~deb13u1
2026-01-29 08:44:04 status half-installed apache2:armhf 2.4.66-1~deb13u1
2026-01-29 08:44:04 status triggers-pending man-db:armhf 2.13.1-1
2026-01-29 08:44:13 status config-files apache2:armhf 2.4.66-1~deb13u1
2026-01-29 08:44:13 status installed apache2-bin:armhf 2.4.66-1~deb13u1
2026-01-29 08:44:13 remove apache2-bin:armhf 2.4.66-1~deb13u1 <none>
2026-01-29 08:44:13 status half-configured apache2-bin:armhf 2.4.66-1~deb13u1
2026-01-29 08:44:13 status half-installed apache2-bin:armhf 2.4.66-1~deb13u1
2026-01-29 08:44:13 status config-files apache2-bin:armhf 2.4.66-1~deb13u1
2026-01-29 08:44:13 status not-installed apache2-bin:armhf <none>
2026-01-29 08:44:13 status installed apache2-data:all 2.4.66-1~deb13u1
2026-01-29 08:44:13 remove apache2-data:all 2.4.66-1~deb13u1 <none>
2026-01-29 08:44:13 status half-configured apache2-data:all 2.4.66-1~deb13u1
2026-01-29 08:44:13 status half-installed apache2-data:all 2.4.66-1~deb13u1
2026-01-29 08:44:13 status config-files apache2-data:all 2.4.66-1~deb13u1
2026-01-29 08:44:13 status not-installed apache2-data:all <none>
2026-01-29 08:44:13 status installed apache2-utils:armhf 2.4.66-1~deb13u1
2026-01-29 08:44:13 remove apache2-utils:armhf 2.4.66-1~deb13u1 <none>
2026-01-29 08:44:13 status half-configured apache2-utils:armhf 2.4.66-1~deb13u1
2026-01-29 08:44:13 status half-installed apache2-utils:armhf 2.4.66-1~deb13u1
2026-01-29 08:44:13 status config-files apache2-utils:armhf 2.4.66-1~deb13u1
2026-01-29 08:44:14 status not-installed apache2-utils:armhf <none>
2026-01-29 08:44:14 startup packages configure
2026-01-29 08:44:14 trigproc man-db:armhf 2.13.1-1 <none>
2026-01-29 08:44:14 status half-configured man-db:armhf 2.13.1-1
2026-01-29 08:44:21 status installed man-db:armhf 2.13.1-1
2026-01-29 08:44:21 startup packages purge
2026-01-29 08:44:22 purge apache2:armhf 2.4.66-1~deb13u1 <none>
2026-01-29 08:44:22 status config-files apache2:armhf 2.4.66-1~deb13u1
2026-01-29 08:44:37 status not-installed apache2:armhf <none>
2026-01-29 08:44:37 startup packages configure


**Package Configs Changed (dpkg -V)**
Note: Lines indicate files differing from package defaults.
??5?????? c /etc/skel/.bashrc
??5?????? c /etc/chromium/master_preferences
??5?????? c /etc/plymouth/plymouthd.conf
??5?????? c /etc/login.defs
??5?????? c /etc/systemd/logind.conf
??5?????? c /etc/xdg/labwc-greeter/environment
??5?????? c /etc/sudoers.d/010_pi-nopasswd
??5??????   /usr/share/firefox/distribution/distribution.ini
??5?????? c /etc/default/useradd
??5?????? c /etc/avahi/avahi-daemon.conf
??5??????   /usr/lib/modprobe.d/g_ether.conf
??5?????? c /etc/initramfs-tools/initramfs.conf
??5?????? c /etc/lightdm/lightdm.conf


**DNS**
/etc/resolv.conf:
# Generated by NetworkManager
search home
nameserver 212.242.40.3
nameserver 212.242.40.51

/etc/hosts:
# Your system has configured 'manage_etc_hosts' as True.
# As a result, if you wish for changes to this file to persist
# then you will need to either
# a.) make changes to the master file in /etc/cloud/templates/hosts.debian.tmpl
# b.) change or remove the value of 'manage_etc_hosts' in
#     /etc/cloud/cloud.cfg or cloud-config from user-data
#
127.0.1.1 packetshop packetshop
127.0.0.1 localhost

# The following lines are desirable for IPv6 capable hosts
::1 localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters



**Nginx**
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful

total 4
-rw-r--r-- 1 root root 523 Jan 29 08:39 fake-internet.conf

--- /etc/nginx/conf.d/fake-internet.conf ---
server {
  listen 80;
  listen [::]:80;
  server_name connectivitycheck.gstatic.com clients3.google.com connectivitycheck.android.com www.gstatic.com www.google.com google.com play.googleapis.com www.samsung.com;

  # Android/Samsung probes -> 204 No Content
  location = /generate_204 { return 204; }
  location = /gen_204 { return 204; }
  location = /android/captive-portal.txt { return 204; }
  location = /ncsi.txt { return 204; }

  # Fallback: lean responses for anything else
  location = / {
    return 204;
  }
}

--- /etc/nginx/sites-enabled/package_shop.conf ---
map $http_upgrade $connection_upgrade { default upgrade; '' close; }

upstream package_shop_api { server 127.0.0.1:5000; }

server {
    listen 443 ssl;
    server_name localhost;

    ssl_certificate     /etc/nginx/certs/server.crt;
    ssl_certificate_key /etc/nginx/certs/server.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass         http://package_shop_api;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection $connection_upgrade;
    }

    # Optional: redirect bare / to staff
    location = / { return 302 /staff; }
}

# Optional: redirect HTTP to HTTPS
server {
    listen 80;
    server_name localhost;
    return 301 https://$host$request_uri;
}


**Apache (presence only)**
total 4
drwxr-xr-x 2 root root 4096 Jan 29 08:44 conf-available

**hostapd / dhcpcd / dnsmasq**
/etc/dhcpcd.conf:
# A sample configuration for dhcpcd.
# See dhcpcd.conf(5) for details.

# Allow users of this group to interact with dhcpcd via the control socket.
#controlgroup wheel

# Inform the DHCP server of our hostname for DDNS.
hostname

# Use the hardware address of the interface for the Client ID.
#clientid
# or
# Use the same DUID + IAID as set in DHCPv6 for DHCPv4 ClientID as per RFC4361.
# Some non-RFC compliant DHCP servers do not reply with this set.
# In this case, comment out duid and enable clientid above.
duid

# Persist interface configuration when dhcpcd exits.
persistent

# vendorclassid is set to blank to avoid sending the default of
# dhcpcd-<version>:<os>:<machine>:<platform>
vendorclassid

# A list of options to request from the DHCP server.
option domain_name_servers, domain_name, domain_search
option classless_static_routes
# Respect the network MTU. This is applied to DHCP routes.
option interface_mtu

# Request a hostname from the network
option host_name

# Most distributions have NTP support.
#option ntp_servers

# A ServerID is required by RFC2131.
require dhcp_server_identifier

# Generate SLAAC address using the Hardware Address of the interface
#slaac hwaddr
# OR generate Stable Private IPv6 Addresses based from the DUID
slaac private


**sysctl**
--- /etc/sysctl.d/98-rpi.conf ---
kernel.printk = 3 4 1 3
vm.min_free_kbytes = 16384
net.ipv4.ping_group_range = 0 2147483647


**Cron**
System cron dirs:
/etc/cron.d:
total 4
-rw-r--r-- 1 root root 188 Jun 10  2025 e2scrub_all

/etc/cron.daily:
total 16
-rwxr-xr-x 1 root root 1478 Jun 24  2025 apt-compat
-rwxr-xr-x 1 root root  123 Jul 31 15:29 dpkg
-rwxr-xr-x 1 root root  377 Jul 14  2024 logrotate
-rwxr-xr-x 1 root root 1395 May  2  2025 man-db

/etc/cron.hourly:
total 0

/etc/cron.monthly:
total 0

/etc/cron.weekly:
total 4
-rwxr-xr-x 1 root root 1055 May  2  2025 man-db

/etc/cron.yearly:
total 0

Root crontab:
No root crontab


**Logs (recent)**
hostapd journal (last 100 lines):
-- No entries --

nginx journal (last 100 lines):
Jan 28 22:13:10 packetshop systemd[1]: Starting nginx.service - A high performance web server and a reverse proxy server...
Jan 28 22:13:11 packetshop systemd[1]: Started nginx.service - A high performance web server and a reverse proxy server.
Jan 29 08:39:59 packetshop systemd[1]: Reloading nginx.service - A high performance web server and a reverse proxy server...
Jan 29 08:40:00 packetshop nginx[4307]: 2026/01/29 08:39:59 [notice] 4307#4307: signal process started
Jan 29 08:40:00 packetshop systemd[1]: Reloaded nginx.service - A high performance web server and a reverse proxy server.

