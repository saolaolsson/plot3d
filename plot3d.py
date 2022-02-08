#!/usr/bin/python3

import direct.showbase.DirectObject
import direct.showbase.ShowBase
import direct.task.TaskManagerGlobal
import panda3d.core as p3d

import numpy as np


def make_axes(
        length = 1.0,
        major_tick_distance=0.1, major_tick_height=0.05,
        minor_tick_distance=0.01, minor_tick_height=0.005):
    def _add_x_tick(linesegs, axis_length, tick_distance, tick_height):
        tick_vector = p3d.Vec3(0, 0, tick_height)
        x = 0
        while abs(x) <= abs(axis_length):
            point = p3d.Vec3(0, 0, 0)
            point[0] = x
            linesegs.move_to(point)
            linesegs.draw_to(point + tick_vector)
            x += tick_distance

    def _make_x_axis(
        color, length,
        major_tick_distance, major_tick_height,
        minor_tick_distance, minor_tick_height):
        ls = p3d.LineSegs()
        ls.set_color(color)
        ls.move_to(0, 0, 0)
        axis_end = p3d.Point3(length, 0, 0)
        ls.draw_to(axis_end)
        _add_x_tick(ls, length, major_tick_distance, major_tick_height)
        _add_x_tick(ls, length, minor_tick_distance, minor_tick_height)
        return ls.create()

    axis = p3d.GeomNode('axis')
    axis.add_geoms_from(_make_x_axis(
        (0.1, 0.1, 0.1, 1), length,
        major_tick_distance, major_tick_height,
        minor_tick_distance, minor_tick_height))
    axis.add_geoms_from(_make_x_axis(
        (0.3, 0.3, 0.3, 1), -length,
        -major_tick_distance, major_tick_height,
        -minor_tick_distance, minor_tick_height))
    axis = p3d.NodePath(axis)

    axes = p3d.NodePath('axes')

    axis_x = axes.attach_new_node('axis_x')
    axis.instance_to(axis_x)

    axis_y = axes.attach_new_node('axis_y')
    axis_y.set_hpr(90, 0, 0)
    axis.instance_to(axis_y)

    axis_z = axes.attach_new_node('axis_z')
    axis_z.set_hpr(180, 0, -90)
    axis.instance_to(axis_z)

    return axes


def make_grid(label, normal, center):
    def _make_grid():
        ls = p3d.LineSegs()

        ls.set_thickness(1)
        ls.set_color(0.35, 0.35, 0.35, 1)
        for x in np.linspace(0, 1, 11, endpoint=True):
            ls.move_to(x, 0, 0)
            ls.draw_to(x, 0, 1)
        for z in np.linspace(0, 1, 11, endpoint=True):
            ls.move_to(0, 0, z)
            ls.draw_to(1, 0, z)
        grid = ls.create()

        ls.set_thickness(2)
        ls.set_color(0.35, 0.35, 0.35, 1)
        ls.move_to(0, 0, 0)
        ls.draw_to(1, 0, 0)
        ls.draw_to(1, 0, 1)
        ls.draw_to(0, 0, 1)
        ls.draw_to(0, 0, 0)

        grid.add_geoms_from(ls.create())
        return grid

    plane = p3d.NodePath(label)
    plane.set_pos(center)
    plane.look_at(normal)

    grid = p3d.NodePath(_make_grid())

    g = plane.attach_new_node('')
    g.set_pos(0, 0, 0)
    grid.instance_to(g)

    g = plane.attach_new_node('')
    g.set_pos(-1, 0, 0)
    grid.instance_to(g)

    g = plane.attach_new_node('')
    g.set_pos(-1, 0, -1)
    grid.instance_to(g)

    g = plane.attach_new_node('')
    g.set_pos(0, 0, -1)
    grid.instance_to(g)

    cn = p3d.CollisionNode('')
    plane.attach_new_node(cn)
    cn.addSolid(p3d.CollisionPolygon(
        (-1, 0, -1), (-1, 0, 1), (1, 0, 1), (1, 0, -1)))

    return plane


def make_cursor(size):
    ls = p3d.LineSegs('cursor')
    ls.set_color(1, 1, 1, 1)
    s = size / 2
    ls.move_to(-s, 0, 0)
    ls.draw_to(s, 0, 0)
    ls.move_to(0, -s, 0)
    ls.draw_to(0, s, 0)
    ls.move_to(0, 0, -s)
    ls.draw_to(0, 0, s)
    return p3d.NodePath(ls.create())


def transform_coordinate_system(point, from_space_node, to_space_node):
    return to_space_node.get_relative_point(from_space_node, point)


def point_ss_to_line_ws(scene, camera, lens, point_ss):
    near = p3d.Point3()
    far = p3d.Point3()
    assert lens.extrude(point_ss, near, far)
    near = transform_coordinate_system(near, camera, scene)
    far = transform_coordinate_system(far, camera, scene)
    return p3d.CollisionLine(camera.get_pos(), far - near)


def pick(scene, camera, lens, mouse_position):
    cn = p3d.CollisionNode('')
    cn.add_solid(point_ss_to_line_ws(scene, camera, lens, mouse_position))
    pick_ray = scene.attach_new_node(cn)

    chq = p3d.CollisionHandlerQueue()
    ct = p3d.CollisionTraverser()
    ct.add_collider(pick_ray, chq)
    ct.traverse(scene)
    pick_ray.remove_node()
    if not chq.entries:
        return None
    chq.sort_entries()
    ce = chq.entries[0]
    if ce.get_surface_point(camera).y < 0:
        return None
    return ce.get_surface_point(scene)


def get_mouse_position(window):
    pointer = window.get_pointer(0)
    window_size = window.get_size()
    position_relative = p3d.Vec2()
    position_relative[0] = 2 * pointer.x / window_size[0] - 1
    position_relative[1] = -(2 * pointer.y / window_size[1] - 1)
    return position_relative


def get_mouse_ticks(pointer, last_position):
    if last_position:
        return p3d.Vec2(pointer.x - last_position.x, pointer.y - last_position.y), pointer
    else:
        return p3d.Vec2(), pointer


def main():
    base = direct.showbase.ShowBase.ShowBase()
    base.disable_mouse()
    base.render.set_antialias(p3d.AntialiasAttrib.MLine)
    base.camLens.set_near(0.01)
    base.camLens.set_far(100)

    make_grid('back', (0, -1, 0), (0, 1, 0)).reparent_to(base.render)
    make_grid('ground', (0, 0, 1), (0, 0, -1)).reparent_to(base.render)
    make_grid('left', (1, 0, 0), (-1, 0, 0)).reparent_to(base.render)
    make_axes(10, 1, 0.05, 0.1, 0.02).reparent_to(base.render)
    make_cursor(0.05).reparent_to(base.render)
    cursor = base.render.find('cursor')

    mouse_wheel_delta = 0
    def _mouse_wheel_listener(delta):
        nonlocal mouse_wheel_delta
        mouse_wheel_delta += delta
    base.accept('wheel_up', lambda: _mouse_wheel_listener(1))
    base.accept('wheel_down', lambda: _mouse_wheel_listener(-1))

    camera = {
        'distance_step': 0.2,
        'speed': 0.01,
        'heading_factor': 0.15,
        'default_position': (0.5, -2, 0.5),
        'default_rotation': (15, -10, 0),
    }
    base.camera.set_pos(camera['default_position'])
    base.camera.set_hpr(camera['default_rotation'])

    is_down = base.mouseWatcherNode.is_button_down

    drag_start_intersection = None
    drag_ground_start_intersection = None
    orbit_start_intersection = None
    while True:
        mouse_position = get_mouse_position(base.win)
        intersection = pick(base.render, base.camera, base.camLens, mouse_position)

        cursor_position = drag_start_intersection or orbit_start_intersection or intersection
        if cursor_position:
            cursor.set_pos(cursor_position)
            cursor.show()
        else:
            cursor.hide()

        # keyboard dolly
        rotate_h = p3d.LRotation(p3d.Vec3.up(), base.camera.get_h())
        camera_forward = rotate_h.xform(p3d.Vec3.forward())
        camera_right = rotate_h.xform(p3d.Vec3.right())
        if is_down(p3d.KeyboardButton.ascii_key('w')):
            base.camera.set_pos(base.camera.get_pos() + camera_forward * camera['speed'])
        if is_down(p3d.KeyboardButton.ascii_key('s')):
            base.camera.set_pos(base.camera.get_pos() - camera_forward * camera['speed'])
        if is_down(p3d.KeyboardButton.ascii_key('d')):
            base.camera.set_pos(base.camera.get_pos() + camera_right * camera['speed'])
        if is_down(p3d.KeyboardButton.ascii_key('a')):
            base.camera.set_pos(base.camera.get_pos() - camera_right * camera['speed'])

        def _mouse_drag(scene, camera, lens, mouse_position, start_intersection, drag_plane_normal):
            drag_plane = p3d.Plane(drag_plane_normal, start_intersection)
            pick_line = point_ss_to_line_ws(scene, camera, lens, mouse_position)
            drag_plane_intersection = p3d.Point3()
            assert drag_plane.intersectsLine(
                drag_plane_intersection,
                pick_line.origin, pick_line.origin + pick_line.direction)
            camera_position_delta = start_intersection - drag_plane_intersection
            base.camera.set_pos(base.camera.get_pos() + camera_position_delta)

        # mouse drag
        if is_down(p3d.MouseButton.one()):
            if not drag_start_intersection and intersection:
                drag_start_intersection = intersection
            if drag_start_intersection:
                _mouse_drag(base.render, base.camera, base.camLens, mouse_position,
                           drag_start_intersection, camera_forward)
        else:
            drag_start_intersection = None

        # mouse drag ground
        if is_down(p3d.MouseButton.two()):
            if not drag_ground_start_intersection and intersection:
                drag_ground_start_intersection = intersection
            if drag_ground_start_intersection:
                _mouse_drag(base.render, base.camera, base.camLens, mouse_position,
                           drag_ground_start_intersection, p3d.Vec3.up())
        else:
            drag_ground_start_intersection = None

        # mouse orbit
        if is_down(p3d.MouseButton.three()):
            if not orbit_start_intersection and intersection:
                orbit_start_intersection = intersection
                orbit_camera_distance = (intersection - base.camera.get_pos()).length()
                orbit_start_mouse_position = mouse_position
                mouse_ticks_context = None
            if orbit_start_intersection:
                mouse_ticks, mouse_ticks_context = \
                    get_mouse_ticks(base.win.get_pointer(0), mouse_ticks_context)
                base.camera.set_hpr(
                    base.camera.get_h() - mouse_ticks[0] * camera['heading_factor'],
                    base.camera.get_p() - mouse_ticks[1] * camera['heading_factor'],
                    base.camera.get_r())
                pick_line = point_ss_to_line_ws(
                    base.render, base.camera, base.camLens, orbit_start_mouse_position)
                base.camera.set_pos(
                    orbit_start_intersection - \
                    pick_line.direction.normalized() * orbit_camera_distance)
        else:
            orbit_start_intersection = None

        # mouse wheel dolly
        if mouse_wheel_delta != 0:
            dolly_vector = point_ss_to_line_ws(
                base.render, base.camera, base.camLens, mouse_position).direction
            base.camera.set_pos(
                base.camera.get_pos() + \
                dolly_vector.normalized() * camera['distance_step'] * mouse_wheel_delta)
            mouse_wheel_delta = 0

        if is_down(p3d.KeyboardButton.ascii_key('q')):
            break
        elif is_down(p3d.KeyboardButton.ascii_key('0')):
            base.camera.set_pos(camera['default_position'])
            base.camera.set_hpr(camera['default_rotation'])

        direct.task.TaskManagerGlobal.taskMgr.step()


if __name__ == '__main__':
    main()
