import argparse

from stable_baselines3 import PPO

import simenv as sm


CAMERA_HEIGHT = 40
CAMERA_WIDTH = 64


def generate_map(index):
    root = sm.Asset(name=f"root_{index}")
    root += sm.Box(
        name=f"floor_{index}",
        position=[0, 0, 0],
        bounds=[-10, 10, 0, 0.1, -10, 10],
        material=sm.Material.BLUE,
        with_collider=True,
    )
    root += sm.Box(
        name=f"wall1_{index}",
        position=[-10, 0, 0],
        bounds=[0, 0.1, 0, 1, -10, 10],
        material=sm.Material.GRAY75,
        with_collider=True,
    )
    root += sm.Box(
        name=f"wall2_{index}",
        position=[10, 0, 0],
        bounds=[0, 0.1, 0, 1, -10, 10],
        material=sm.Material.GRAY75,
        with_collider=True,
    )
    root += sm.Box(
        name=f"wall3_{index}",
        position=[0, 0, 10],
        bounds=[-10, 10, 0, 1, 0, 0.1],
        material=sm.Material.GRAY75,
        with_collider=True,
    )
    root += sm.Box(
        name=f"wall4_{index}",
        position=[0, 0, -10],
        bounds=[-10, 10, 0, 1, 0, 0.1],
        material=sm.Material.GRAY75,
        with_collider=True,
    )

    actor = sm.EgocentricCameraActor(position=[0.0, 0.5, 0.0], camera_width=64, camera_height=40)
    root += actor
    mass = 0.2
    target = sm.Box(
        name=f"target_{index}",
        position=[-2, 0.5, 2],
        material=sm.Material.RED,
        physics_component=sm.RigidBodyComponent(mass=mass),
    )
    root += target
    target_reward = sm.RewardFunction(
        type="see",
        entity_a=actor,
        entity_b=target,
        distance_metric="euclidean",
        threshold=30.0,
        is_terminal=True,
        is_collectable=True,
        scalar=1.0,
        trigger_once=True,
    )
    actor += target_reward

    return root


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build_exe", default=None, type=str, required=False, help="Pre-built unity app for simenv")
    parser.add_argument("--n_maps", default=12, type=int, required=False, help="Number of maps to spawn")
    parser.add_argument("--n_show", default=4, type=int, required=False, help="Number of maps to show")
    args = parser.parse_args()

    env = sm.RLEnv(generate_map, args.n_maps, args.n_show, engine_exe=args.build_exe)

    # for i in range(1000):
    #     obs, reward, done, info = env.step()
    model = PPO("MultiInputPolicy", env, verbose=3, n_epochs=1)
    model.learn(total_timesteps=100000)

    env.close()
