import os.path

import pygame
import math
import functools


def smear(img: pygame.Surface):
    yaxis = [0] * img.get_height()
    xaxis = [0] * img.get_width()
    for y in range(img.get_height()):
        for x in range(img.get_width()):
            px = sum(img.get_at((x, y)).rgb) / 3
            xaxis[x] += px / 255
            yaxis[y] += px / 255
    yaxis = [val / img.get_width() for val in yaxis]
    xaxis = [val / img.get_height() for val in xaxis]
    return xaxis, yaxis


def multismear(imgs):
    tot_yaxis = [0] * imgs[0].get_height()
    tot_xaxis = [0] * imgs[0].get_width()
    for img in imgs:
        xaxis, yaxis = smear(img)
        for x in range(len(xaxis)):
            tot_xaxis[x] += xaxis[x]
        for y in range(len(yaxis)):
            tot_yaxis[y] += yaxis[y]
    for x in range(len(tot_xaxis)):
        tot_xaxis[x] /= len(imgs)
    for y in range(len(tot_yaxis)):
        tot_yaxis[y] /= len(imgs)
    return tot_xaxis, tot_yaxis


def find_rects(img):
    rects = []
    q = [(0, 0)]
    seen = set()
    seen.add(q[0])
    while len(q) > 0:
        x, y = q.pop(-1)
        for (nx, ny) in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
            if nx < 0 or nx >= img.get_width() or ny < 0 or ny >= img.get_height():
                continue
            elif (nx, ny) in seen:
                continue
            elif sum(img.get_at((nx, ny)).rbg) // 3 == 255:
                seen.add((nx, ny))
                q.append((nx, ny))
            else:
                seen.add((nx, ny))
                rect = fill(img, (nx, ny), seen, lambda px: px < 255)
                rects.append(rect)

    def _cmp(a, b):
        if b[1] >= a[1] + a[3]:
            return -1
        elif a[1] >= b[1] + b[3]:
            return 1
        else:
            return -1 if b[0] > a[0] else (0 if b[0] == a[0] else 1)

    return list(sorted(rects, key=functools.cmp_to_key(_cmp)))


def fill(img, start, seen, cond):
    min_x = start[0]
    max_x = start[0]
    min_y = start[1]
    max_y = start[1]
    q = [start]
    while len(q) > 0:
        x, y = q.pop(-1)
        for (nx, ny) in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
            if nx < 0 or nx >= img.get_width() or ny < 0 or ny >= img.get_height():
                continue
            elif (nx, ny) in seen:
                continue
            elif not cond(sum(img.get_at((nx, ny)).rbg) // 3):
                continue
            else:
                q.append((nx, ny))
                seen.add((nx, ny))
                min_x = min(min_x, nx)
                max_x = max(max_x, nx)
                min_y = min(min_y, ny)
                max_y = max(max_y, ny)

    return [min_x, min_y, max_x - min_x + 1, max_y - min_y + 1]


class Glyph:

    def __init__(self, img: pygame.Surface, src=None, pos=None, page_num=None):
        self.img = img
        self.src = src
        self.pos = pos
        self.page_num = page_num
        self._id = self._calc_id()

    def get_id(self):
        return self._id

    def _calc_id(self):
        ret = [0] * (self.img.get_width() * self.img.get_height())
        for y in range(self.img.get_height()):
            for x in range(self.img.get_width()):
                val = sum(self.img.get_at((x, y)).rgb) // 3
                ret[y * self.img.get_width() + x] = val
        return tuple(ret)

    def get_thumbnail(self, icing=(1, 2, 1, 4)):
        if self.src is None or self.pos is None:
            return self.img
        else:
            x1 = max(0, self.pos[0] - icing[0])
            x2 = min(self.pos[0] + self.pos[2] + icing[0] + icing[2], self.src.get_width())
            y1 = max(0, self.pos[1] - icing[1])
            y2 = min(self.pos[1] + self.pos[3] + icing[1] + icing[3], self.src.get_height())
            return self.src.subsurface((x1, y1, x2 - x1, y2 - y1))

    def __eq__(self, other):
        return self.get_id() == other.get_id()

    def __hash__(self):
        return hash(self.get_id())


def process_pages(filenames, text_area, white_thresh=0.95, use_for_rect_detection=()):
    imgs = [pygame.image.load(filename).subsurface(text_area) for filename in filenames]

    for_rects = [imgs[i] for i in range(len(filenames))
                 if (filenames[i] in use_for_rect_detection or len(use_for_rect_detection) == 0)]
    xaxis, yaxis = multismear(for_rects)

    smeared = pygame.Surface(imgs[0].get_size())
    for y in range(imgs[0].get_height()):
        for x in range(imgs[0].get_width()):
            if xaxis[x] > white_thresh or yaxis[y] > white_thresh:
                val = 255
            else:
                val = int((xaxis[x] * yaxis[y]) * 255)
            smeared.set_at((x, y), (val, val, val))

    rects = find_rects(smeared)

    res = {
        'imgs': imgs,
        'glyphs': [],
        'xaxis': xaxis,
        'yaxis': yaxis,
        'smeared': smeared,
        'rects': rects
    }

    for idx, img in enumerate(imgs):
        for r in rects:
            res['glyphs'].append(Glyph(img.subsurface(r), src=img, pos=r, page_num=idx))

    return res


if __name__ == "__main__":

    files = [f"input/EFTA00756980-{i}.png" for i in range(7)]
    output = process_pages(files, [33, 40, 750, 983], use_for_rect_detection=(
        "input/EFTA00756980-1.png",
        "input/EFTA00756980-2.png"))

    glyphs = []
    seen = set()
    unique_glyphs = []
    for glyph in output['glyphs']:
        glyphs.append(glyph)
        if glyph not in seen:
            seen.add(glyph)
            unique_glyphs.append(glyph)

    print(f"Found {len(glyphs)} glyphs ({len(unique_glyphs)} unique).")

    meanings = ""
    if os.path.exists("glyph_map.txt"):
        with open("glyph_map.txt") as f:
            meanings = "".join(line.rstrip() for line in f.readlines())
        print(f"Read {len(meanings)} definitions from glyph_map.txt")
    glyph_meanings = {}

    panel_size = (10, 16)
    dims = (round(0.5 + math.sqrt(len(unique_glyphs))), round(0.5 + math.sqrt(len(unique_glyphs))))
    glyph_map = pygame.Surface((dims[0] * panel_size[0], dims[1] * panel_size[1]))
    glyph_map.fill("cyan")
    for i, g in enumerate(unique_glyphs):
        x = (i % dims[0]) * panel_size[0]
        y = (i // dims[0]) * panel_size[1]
        thumb = g.get_thumbnail()
        glyph_map.blit(thumb, (x, y))

        if i < len(meanings):
            glyph_meanings[g] = meanings[i]

    pygame.image.save(glyph_map, "glyph_map.png")
    print(f"Wrote: glyph_map.png")

    if len(meanings) > 0:
        out_text = []
        cur_line = []
        unknown_symbols = 0
        for i in range(len(glyphs)):
            if i > 0 and (glyphs[i].pos[1] > glyphs[i - 1].pos[1] + glyphs[i - 1].pos[3]
                          or glyphs[i].page_num > glyphs[i-1].page_num):
                out_text.append("".join(cur_line).rstrip())
                cur_line = []
            if glyphs[i] in glyph_meanings:
                cur_line.append(glyph_meanings[glyphs[i]])
            else:
                unknown_symbols += 1
                cur_line.append("?")
        out_text.append("".join(cur_line))

        with open("output/plaintext.txt", 'w') as f:
            for line in out_text:
                f.write(f"{line}\n")
            print(f"Wrote: plaintext.txt (with {unknown_symbols} unknown symbol(s))")

    screen = pygame.display.set_mode((600, 600), pygame.RESIZABLE)
    page_idx = 0
    mode_idx = 0
    modes = ["normal", "smeared", "rects"]

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                raise SystemExit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    raise SystemExit()
                elif e.key == pygame.K_SPACE:
                    mode_idx = (mode_idx + 1) % len(modes)
                elif e.key == pygame.K_LEFT:
                    page_idx = (page_idx - 1) % len(output['imgs'])
                elif e.key == pygame.K_RIGHT:
                    page_idx = (page_idx + 1) % len(output['imgs'])

        screen.fill("black")

        mode = modes[mode_idx]
        if mode == 'normal':
            screen.blit(output['imgs'][page_idx], (0, 0))
        elif mode == 'smeared':
            screen.blit(output['smeared'], (0, 0))
        elif mode == 'rects':
            screen.blit(output['smeared'], (0, 0))
            for idx, r in enumerate(output['rects']):
                color = (int(idx / len(output['rects']) * 255),) * 3
                pygame.draw.rect(screen, color, r)

        elapsed_time_ms = pygame.time.get_ticks()
        i = elapsed_time_ms // 100

        scr_w, scr_h = screen.get_size()

        pygame.display.flip()

