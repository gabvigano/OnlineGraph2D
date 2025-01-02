import math

import pygame

from OnlineGraph2d.Graphics import generate_shape
from OnlineGraph2d.Network import Server, Client, get_ip
from OnlineGraph2d.Physics import GameObject, Camera, Rope, Follower, grappling_gun_check

host_type = input('who are you? [server/client]: ').lower()
port = 5555

if host_type == 'server':
    print('\nsetting up server...')

    server_ip = get_ip()

    if not server_ip:
        print('error: failed to get the ip address')
    else:
        print(f'server started: the server ip is: {server_ip}')

        server = Server(server_ip=server_ip, port=port)

elif host_type == 'client':
    server_ip = input('\nenter the server ip: ')

    client = Client(server_ip=server_ip, port=port)

else:
    print('\nhost type not valid')
    exit()

host = server if host_type == 'server' else client  # noqa

pygame.init()

screen_size = (1600, 900)
FPS = 120
display = pygame.display.set_mode(screen_size)
pygame.display.set_caption(host_type + ('_' + str(host.client_number) if host_type == 'client' else ''))
clock = pygame.time.Clock()
text_font = pygame.font.SysFont('dejavusansmono', 15)

close = False
objects = {}
colors_rgb = [
    (0, 255, 0),  # green
    (0, 0, 255),  # blue
    (255, 255, 0),  # yellow
    (255, 0, 0),  # red
    (255, 100, 0),  # orange
    (128, 0, 128),  # purple
    (165, 42, 42),  # brown
    (255, 255, 255)  # white
]
grappling_gun_target = None
grappling_gun_swing = False
mouse_pos = None

game_map = [
    GameObject(pos=(0, screen_size[1] - 100), angle=0, size=(screen_size[0], 50), shape='rect', color=(255, 255, 255), layer=0, static=True),
    GameObject(pos=(600, screen_size[1] - 600), angle=0, size=(50, 50), shape='rect', color=(255, 255, 255), layer=0, static=True),
    GameObject(pos=(100, screen_size[1] - 300), angle=0, size=(200, 200), shape='rect', color=(255, 255, 255), layer=0, static=True)
]
game_map_collision = [(map_obj.pos, map_obj.size) for map_obj in game_map]

player = GameObject(pos=[100, 100], angle=0, size=(30, 30), shape='circle', color=colors_rgb[host.client_number], layer=2, static=False, mass=1, collision=game_map_collision)
camera = Camera(obj=player, screen_size=screen_size)
gun = Follower(obj=player, rel_pos=[player.size[0] - 7, player.size[1] / 2 - 3], angle=0, size=(15, 6), shape='rect', color=(100, 100, 100), layer=5)

if host_type == 'server':
    local_objects = [player, gun]
    objects = {host.client_number: local_objects}
else:
    local_objects = [player, gun]

while not close:
    # clear display and show fps
    display.fill((0, 0, 0))
    display.blit(text_font.render(f'FPS: {clock.get_fps():.1f} / {FPS}', 1, (255, 255, 255)), (screen_size[0] - 170, 25))

    # check if the window is closed
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            close = True

        # check if the mouse button is pressed for the grappling gun
        mouse_pos = pygame.mouse.get_pos()
        mouse_camera_pos = (mouse_pos[0] + camera.pos[0], mouse_pos[1] + camera.pos[1])
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                grappling_gun_target = mouse_camera_pos
                grappling_gun_swing = True
            elif event.button == 3:
                grappling_gun_target = mouse_camera_pos
                grappling_gun_swing = False

    # update mouse position based on the camera movement
    mouse_camera_pos = (mouse_pos[0] + camera.pos[0], mouse_pos[1] + camera.pos[1])

    # grappling gun
    if grappling_gun_target is not None:
        if not grappling_gun_check(mouse_pos=grappling_gun_target, collision=player.collision):
            grappling_gun_target = None
            player.rope = None
        else:
            if player.rope and ((not pygame.mouse.get_pressed()[0] and player.rope.swing) or (not pygame.mouse.get_pressed()[2] and not player.rope.swing)):
                # release grappling gun
                if not player.rope.swing:
                    player.apply_vel(vel=20, angle=-player.rope.angle - math.pi / 2)
                grappling_gun_target = None
                player.rope = None
            else:
                if not player.rope:
                    player.rope = Rope(obj=player, pivot=grappling_gun_target, color=player.color, swing=grappling_gun_swing)

    # check keyboard keys for movement
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LSHIFT]:
        run = True
    else:
        run = False

    if keys[pygame.K_w] and player.can_jump:
        player.apply_axis_vel(vel=-8, axis=1)
    if keys[pygame.K_d]:
        player.apply_axis_vel(vel=1, axis=0, limit=5) if run else player.apply_axis_vel(vel=1, axis=0, limit=3)
    if keys[pygame.K_a]:
        player.apply_axis_vel(vel=-1, axis=0, limit=-5) if run else player.apply_axis_vel(vel=-1, axis=0, limit=-3)
    if keys[pygame.K_r]:
        player.pos = [100, 100]
        player.vel = [0, 0]

    # transfer data
    if host_type == 'server':
        other_data = host.send(objects)
        objects = {host.client_number: local_objects} | other_data
        pass
    else:
        objects = host.send(local_objects)
        objects = {host_number: host_objs for host_number, host_objs in objects.items() if host_number != host.client_number}

    # update player collision
    player.collision = game_map_collision + [(obj.pos, obj.size) for host_number, host_objs in objects.items() for obj in host_objs if host_number != host.client_number]

    # compute positions
    for game_obj in local_objects:
        game_obj.update()
    camera.update()
    if not player.rope:
        gun.angle = math.atan2(mouse_camera_pos[1] - gun.pos[1] + gun.size[1] / 2, mouse_camera_pos[0] - gun.pos[0] + gun.size[0] / 2)  # noqa
    else:
        gun.angle = math.atan2(grappling_gun_target[1] - gun.pos[1] + gun.size[1] / 2, grappling_gun_target[0] - gun.pos[0] + gun.size[0] / 2)  # noqa

    player.render_vel(display=display, camera=camera, double=False)

    # display objects
    render_objs = []
    render_objs.extend(game_map)
    if host_type == 'client':
        render_objs.extend(local_objects)
    for host_objs in objects.values():
        render_objs.extend(host_objs)

    render_objs.sort(key=lambda obj: obj.layer)  # sort objects by layer

    for obj in render_objs:
        try:
            if obj.rope:
                obj.rope.blit(display=display, camera=camera)
        except AttributeError:
            pass
        display.blit(*generate_shape(obj=obj, camera=camera))

    # display variables
    variables = {
        'rope_angle ': player.rope.angle if player.rope else None,
        'rope_length': player.rope.length if player.rope else None,
        'ang_vel    ': player.ang_vel,
        'ang_acc    ': player.ang_acc
    }
    y = 25
    for name, value in variables.items():
        try:
            display.blit(text_font.render(f'{name}: {value}', 1, (255, 255, 255)), (25, y))
        except Exception as e:  # noqa
            display.blit(text_font.render(f'{name}: None', 1, (255, 255, 255)), (25, y))
            print(e)
        y += 25

    # render
    pygame.display.update()
    clock.tick(FPS)

pygame.quit()
