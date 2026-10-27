// Q3: Packet loss at a bottleneck.  A,B --(100Mbps,2ms)--> Router --(bottleneck,10ms)--> Receiver
// Run: ./ns3 run "scratch/q3-bottleneck --rate=10Mbps"   then   --rate=1Mbps
#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/traffic-control-module.h"
#include <fstream>
using namespace ns3;

uint32_t drops = 0;
void OnDrop(Ptr<const QueueDiscItem>) { drops++; }

int main(int argc, char* argv[])
{
    std::string rate = "10Mbps", sendRate = "4Mbps";
    CommandLine cmd;
    cmd.AddValue("rate", "Bottleneck link rate", rate);
    cmd.AddValue("sendRate", "UDP rate per sender", sendRate);
    cmd.Parse(argc, argv);
    Config::SetDefault("ns3::PfifoFastQueueDisc::MaxSize", StringValue("100p")); // router buffer

    NodeContainer n;
    n.Create(4); // 0 = Sender A, 1 = Sender B, 2 = Router, 3 = Receiver
    PointToPointHelper link;
    link.SetQueue("ns3::DropTailQueue<Packet>", "MaxSize", StringValue("10p"));
    link.SetDeviceAttribute("DataRate", StringValue("100Mbps"));
    link.SetChannelAttribute("Delay", StringValue("2ms"));
    NetDeviceContainer dA = link.Install(n.Get(0), n.Get(2));
    NetDeviceContainer dB = link.Install(n.Get(1), n.Get(2));
    link.SetDeviceAttribute("DataRate", StringValue(rate));
    link.SetChannelAttribute("Delay", StringValue("10ms"));
    NetDeviceContainer dR = link.Install(n.Get(2), n.Get(3));

    InternetStackHelper().Install(n);
    Ipv4AddressHelper ip;
    ip.SetBase("10.1.1.0", "255.255.255.0"), ip.Assign(dA);
    ip.SetBase("10.1.2.0", "255.255.255.0"), ip.Assign(dB);
    ip.SetBase("10.1.3.0", "255.255.255.0");
    Ipv4Address rx = ip.Assign(dR).GetAddress(1);
    Ipv4GlobalRoutingHelper::PopulateRoutingTables();

    for (uint16_t i = 0; i < 2; i++) // each sender -> its own sink port on the Receiver
    {
        uint16_t port = 9000 + i;
        PacketSinkHelper("ns3::UdpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), port)).Install(n.Get(3));
        OnOffHelper src("ns3::UdpSocketFactory", InetSocketAddress(rx, port));
        src.SetConstantRate(DataRate(sendRate), 1024);
        ApplicationContainer app = src.Install(n.Get(i));
        app.Start(Seconds(1.0 + i * 0.0005)); // small offset so the CBR streams aren't phase-locked
        app.Stop(Seconds(11.0));              // 10 s of traffic
    }

    n.Get(2)->GetObject<TrafficControlLayer>()->GetRootQueueDiscOnDevice(dR.Get(0))
        ->TraceConnectWithoutContext("Drop", MakeCallback(&OnDrop));
    FlowMonitorHelper fmh;
    Ptr<FlowMonitor> fm = fmh.InstallAll();
    Simulator::Stop(Seconds(14.0)); // extra time lets the queue drain
    Simulator::Run();

    std::ofstream csv("q3_results.csv", std::ios::app);
    if (csv.tellp() == 0)
        csv << "bottleneck,flow,tx_pkts,rx_pkts,lost_pkts,loss_pct,throughput_Mbps,avg_delay_ms\n";
    auto cls = DynamicCast<Ipv4FlowClassifier>(fmh.GetClassifier());
    for (auto& [id, s] : fm->GetFlowStats())
    {
        std::string flow = cls->FindFlow(id).destinationPort == 9000 ? "A" : "B";
        uint32_t lost = s.txPackets - s.rxPackets;
        double thr = s.rxBytes * 8.0 / 10.0 / 1e6;                         // Mbps over 10 s
        double dly = s.rxPackets ? 1e3 * s.delaySum.GetSeconds() / s.rxPackets : 0; // ms
        csv << rate << "," << flow << "," << s.txPackets << "," << s.rxPackets << "," << lost << ","
            << 100.0 * lost / s.txPackets << "," << thr << "," << dly << "\n";
        std::cout << rate << " Sender " << flow << ": tx=" << s.txPackets << " rx=" << s.rxPackets
                  << " lost=" << lost << " thr=" << thr << " Mbps delay=" << dly << " ms\n";
    }
    std::cout << "Router queue drops: " << drops << "\n";
    Simulator::Destroy();
}
