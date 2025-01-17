import math

import pygame

from OnlineGraph2d.Physics import FollowerObject


def generate_shape(obj, camera):
    image = pygame.Surface(obj.size, pygame.SRCALPHA)

    if obj.shape == 'rect':
        pygame.draw.rect(image, obj.color, image.get_rect())
    elif obj.shape == 'circle':
        pygame.draw.circle(image, obj.color, (obj.size[0] // 2, obj.size[1] // 2), obj.size[0] / 2)

    if obj.angle != 0 and obj.shape != 'circle':
        image = pygame.transform.rotate(image, -math.degrees(obj.angle))
        rect = image.get_rect()

        if isinstance(obj, FollowerObject):  # if it is a Follower instance it rotates around the main object's center
            main_vect = pygame.math.Vector2(obj.obj.pos[0] + obj.obj.size[0] / 2, obj.obj.pos[1] + obj.obj.size[1] / 2)
            obj_vect = pygame.math.Vector2(obj.pos[0] + obj.size[0] / 2, obj.pos[1] + obj.size[1] / 2)
            new_pos = (obj_vect - main_vect).rotate(math.degrees(obj.angle)) + main_vect
            rect.center = new_pos  # noqa
            pos = rect.topleft
        else:  # otherwise it rotates around its center
            rect.center = (obj.pos[0] + obj.size[0] / 2, obj.pos[1] + obj.size[1] / 2)
            pos = rect.topleft
    else:
        pos = obj.pos

    pos = (pos[0] - camera.pos[0], pos[1] - camera.pos[1])

    # center
    if obj.centered:
        pos = (pos[0] - obj.size[0] / 2, pos[1] - obj.size[1] / 2)

    return image, pos
