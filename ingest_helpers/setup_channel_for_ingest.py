# Copyright 2016 The Johns Hopkins University Applied Physics Laboratory
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import json
from intern.remote.boss import BossRemote
from intern.resource.boss.resource import *
import argparse


if __name__ == '__main__':

    # Command line parser
    parser = argparse.ArgumentParser(description='Creates a collection, coord, experiment and a channel to upload a data to the BOSS.')
    parser.add_argument('-c', '--conf_file', type=str,
                        help='The json configuration file that contains the information needed for the collection, coord, experiment and channel that need to be created. (default: db_configs/demo_cfg.json).',
                        default=os.path.join('db_configs', 'demo_cfg.json'))
    parser.add_argument('-b', '--boss_conf_file', type=str,
                        help='The configuration file that contains the boss connection and token information. (default: boss.cfg).',
                        default='boss.cfg')
    parser.add_argument('--ingest_configs_dir', type=str,
                        help='The directory where the ingest configuration file (written in the conf_file) should be located. (default: ingest_configs).',
                        default='ingest_configs')
    args = parser.parse_args()

    # Load Configuration File
    with open(args.conf_file, 'rt') as cfg:
        config = json.load(cfg)

    rmt = BossRemote(args.boss_conf_file)

    # Create a collection
    collection = CollectionResource(config["collection"]["name"], config["collection"]["description"])
    try:
        collection = rmt.create_project(collection)
    except Exception as e:
        collection = rmt.get_project(collection)

    # Create a coord frame
    coord = CoordinateFrameResource(config["coordinate_frame"]["name"],
                                    config["coordinate_frame"]["description"],
                                    config["coordinate_frame"]["x_start"],
                                    config["coordinate_frame"]["x_stop"],
                                    config["coordinate_frame"]["y_start"],
                                    config["coordinate_frame"]["y_stop"],
                                    config["coordinate_frame"]["z_start"],
                                    config["coordinate_frame"]["z_stop"],
                                    config["coordinate_frame"]["voxel_size_x"],
                                    config["coordinate_frame"]["voxel_size_y"],
                                    config["coordinate_frame"]["voxel_size_z"])
    try:
        coord = rmt.create_project(coord)
    except:
        coord = rmt.get_project(coord)

    # Create an experiment
    if "num_time_samples" not in config["experiment"]:
        num_time_samples = 1
    else:
        num_time_samples = config["experiment"]["num_time_samples"]

    experiment = ExperimentResource(config["experiment"]["name"], collection.name, coord.name,
                                    config["experiment"]["description"],
                                    num_time_samples=num_time_samples)
    try:
        experiment = rmt.create_project(experiment)
    except:
        experiment = rmt.get_project(experiment)

    # Create a channel
    if "sources" not in config["channel"]:
        sources = []
    else:
        sources = config["channel"]["sources"]

    channel = ChannelResource(config["channel"]["name"], collection.name, experiment.name,
                              type=config["channel"]["type"], description=config["channel"]["description"],
                              datatype=config["channel"]["datatype"], sources=sources)
    try:
        channel = rmt.create_project(channel)
    except:
        channel = rmt.get_project(channel)

    # Add gov team permissions
    rmt.add_permissions('gov_team', collection, ['read'])
    rmt.add_permissions('gov_team', experiment, ['read'])
    rmt.add_permissions('gov_team', channel, ['read'])

    # Update ingest file with resources names from config file
    with open(os.path.join(args.ingest_configs_dir, config['ingest_cfg']), 'rt') as cfg:
        ingest_file = json.load(cfg)
        ingest_file['database']['collection'] = collection.name
        ingest_file['database']['experiment'] = experiment.name
        ingest_file['database']['channel'] = channel.name

    with open(os.path.join(args.ingest_configs_dir, config['ingest_cfg']), 'wt') as cfg:
        json.dump(ingest_file, cfg, indent=2)

    print("\n\nRun this command in the ingest-client repo directory to execute the ingest client:")
    print("\n  export INTERN_TOKEN={}".format(rmt.project_service.auth))
    print("  python client.py {}".format(os.path.abspath(os.path.join(args.ingest_configs_dir, config['ingest_cfg']))))

