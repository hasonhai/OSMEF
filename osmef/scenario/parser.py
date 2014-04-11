from configparser import ConfigParser
import logging
import os
import osmef.openstack
import osmef.ssh
import osmef.command_proto
import osmef.nodes
log = logging.getLogger(__name__)


class ScenarioManager:
    def __init__(self):
        self.scenarios_avail = {}
        openstack_conffile = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "openstack.conf"))
        self.scenario_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "conf"))
        self.default_cfg_file = os.path.join(self.scenario_dir, "defaults.cfg")
        self._scan()
        self.active = None
        self.vm_setup = []
        self.openstack = osmef.openstack.OpenStack(openstack_conffile)

    def _scan(self):
        for f in os.listdir(self.scenario_dir):
            if f[-5:] != ".scen":
                continue
            self._load_one(f)

    def _load_one(self, scen_file):
        scen = ConfigParser()
        scen.read_file(open(self.default_cfg_file))
        scen.read(os.path.join(self.scenario_dir, scen_file))
        name = scen.get("description", "name")
        if name is None:
            log.warning("Invalid scenario: %s" % scen_file)
            return
        self.scenarios_avail[name] = scen

    def list_available(self):
        return self.scenarios_avail.keys()

    def select(self, scenario):
        if self.active is not None:
            raise RuntimeError("A scenario is already active")

        self.active = self.scenarios_avail[scenario]
        log.info("Selected scenario '%s'" % scenario)

        num_vms = int(self.active.get("description", "num_vms"))
        for i in range(1, num_vms + 1):
            vm = {}
            vm["name"] = "vm%d" % i
            vm["flavor"] = self.active.get("vm", "flavor")
            vm["image"] = self.active.get("vm", "image")
            vm["key"] = self.active.get("vm", "key")
            vm["keyfile"] = self.active.get("vm", "keyfile")
            vm["username"] = self.active.get("vm", "username")
            vm["base_mapper_port"] = int(self.active.get("vm", "base_mapper_port"))
            vm["zone"] = self.active.get("vm%d" % i, "zone")
            vm["num_mappers"] = int(self.active.get("vm%d" % i, "num_mappers"))
            vm["num_reducers"] = int(self.active.get("vm%d" % i, "num_reducers"))
            self.vm_setup.append(vm)

        self.openstack.spawn_vms(self.vm_setup)
        osmef.ssh.wait_boot(self.vm_setup)
        osmef.ssh.put_workers(self.vm_setup)
        osmef.ssh.start_workers(self.vm_setup)

        self.distribute_workload()

        osmef.command_proto.init(self.vm_setup)

    def distribute_workload(self):
        total_mappers = 0
        total_reducers = 0
        mapper_ips = []
        for vm in self.vm_setup:
            vm["mappers"] = []
            vm["reducers"] = []
            total_reducers += vm["num_reducers"]
            total_mappers += vm["num_mappers"]
            for i in range(vm["num_mappers"]):
                # mapper IP, number of incoming connections, bytes assigned to this mapper, listen port, num_reducers
                m = osmef.nodes.Mapper()
                m.ip = vm["ip"]
                m.max_incoming_conn = int(self.active.get("node", "num_conn_rx"))
                m.port = vm["base_mapper_port"] + i
                vm["mappers"].append(m)
                mapper_ips.append((m.ip, m.port))
            for i in range(vm["num_reducers"]):
                r = osmef.nodes.Reducer()
                r.max_outgoing_conn = int(self.active.get("node", "num_conn_tx"))
                # list of mapper IPs, number of outgoing connections
                vm["reducers"].append(r)

        shuffle_size = int(self.active.get("description", "total_shuffle_size")) * 1024 * 1024 * 1024
        per_mapper_size = shuffle_size / total_mappers
        per_reducer_size = per_mapper_size / total_reducers

        for vm in self.vm_setup:
            for m in vm["mappers"]:
                m.reducer_sizes = [per_reducer_size] * total_reducers
            for r in vm["reducers"]:
                r.mapper_ips = mapper_ips

    def start(self):
        osmef.command_proto.start_measurement(self.vm_setup)

    def scenario_end(self):
        osmef.command_proto.end(self.vm_setup)
        logs = osmef.ssh.get_worker_logs(self.vm_setup)
        for l in logs:
            print("==> {} <==\n{}\n\n".format(l, logs[l].decode("utf-8")))

    def cleanup(self):
        if self.active is None:
            return

        self.openstack.terminate_vms(self.vm_setup)
        self.active = None

