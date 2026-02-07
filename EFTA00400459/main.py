import pygame
import base64
import re

PATHS = "input\\EFTA00400459-XXX.png"
OUTPUT = "output"

N = 76

GRID_PX_OFFS = (61, 39)
GRID_PX_SIZE = (7.8, 15)
GRID_DIMS = 76, 65  # per page

GLYPH_RECT = (1, 2, 8 - 2, 15 - 4)

# small portion of the code that appears on the first page
P0_CODE = "JVBERi0xLjUNJeLjz9MNCjM0IDAgb2JqDTw8L0xpbmVhcml6ZWQgMS9MIDI3NjAyOC9PIDM2L0Ug"

GLYPH_IDS = {}


class Page:

    def __init__(self, filename):
        self.filename = filename
        self.raw = pygame.image.load(filename)
        self._all_glyphs = None

    def get_grid_rect(self, x, y, width=1, height=1):
        x1 = round(GRID_PX_OFFS[0] + x * GRID_PX_SIZE[0])
        y1 = round(GRID_PX_OFFS[1] + y * GRID_PX_SIZE[1])
        x2 = round(GRID_PX_OFFS[0] + (x + width) * GRID_PX_SIZE[0])
        y2 = round(GRID_PX_OFFS[1] + (y + height) * GRID_PX_SIZE[1])
        return x1, y1, x2 - x1 if width > 1 else round(GRID_PX_SIZE[0]), y2 - y1

    def get_grid_img(self, x, y, width=1, height=1):
        return self.raw.subsurface(self.get_grid_rect(x, y, width=width, height=height))

    def get_glyph_at(self, x, y):
        if self._all_glyphs is None:
            self.all_glyphs()
        if (x, y) in self._all_glyphs:
            return self._all_glyphs[(x, y)]
        return None

    def all_glyphs(self):
        if self._all_glyphs is None:
            self._all_glyphs = {}
            for y in range(GRID_DIMS[1]):
                for x in range(GRID_DIMS[0]):
                    self._all_glyphs[(x, y)] = Glyph(self.get_grid_img(x, y), (x, y))
        return self._all_glyphs.values()


class Glyph:

    def __init__(self, surf, xy):
        self.raw = surf
        self.vector = Glyph.vectorize(surf, GLYPH_RECT)
        self.xy = xy

        if self.vector not in GLYPH_IDS:
            GLYPH_IDS[self.vector] = len(GLYPH_IDS)

    def get_id(self):
        return GLYPH_IDS[self.vector]

    def __eq__(self, other):
        return self.vector == other.vector

    def __hash__(self):
        return hash(self.vector)

    @staticmethod
    def vectorize(img: pygame.Surface, rect):
        ret = [0] * rect[2] * rect[3]
        for i in range(rect[2] * rect[3]):
            ret[i] = int(sum(img.get_at((rect[0] + i % rect[2], rect[1] + i // rect[2])).rgb) / 3)
        return tuple(ret)


def load_pngs():
    res = []
    for i in range(N):
        path = PATHS.replace("XXX", str(i).zfill(3))
        print(f"Loading: {path}")
        res.append(Page(path))
    return res


def load_mappings():
    res = {}
    print("Loading mappings.txt")
    with open("mappings.txt") as file:
        while line := file.readline():
            try:
                line = line.rstrip()
                if len(line) == 0:
                    continue
                char = line[0]
                nums = line[4:len(line)-1].split(", ")
                nums = tuple([int(v) for v in nums])

                if char != "?":
                    res[nums] = char
            except ValueError:
                pass
    return res


if __name__ == "__main__":
    pygame.init()

    pages = load_pngs()
    mappings = load_mappings()

    print("Processing glyphs...")
    ordered_glyphs = []
    glyphs = {}
    for p in pages[1:]:
        for g in p.all_glyphs():
            ordered_glyphs.append(g)
            if g not in glyphs:
                if g.vector not in mappings:
                    glyphs[g] = "?"
                else:
                    glyphs[g] = mappings[g.vector]

    flipped_glyphs = {}
    for g in glyphs:
        if glyphs[g] not in flipped_glyphs:
            flipped_glyphs[glyphs[g]] = []
        flipped_glyphs[glyphs[g]].append(g)

    print(f"\nTotal glyph count: {len(ordered_glyphs)}")
    print(f"Unique glyphs: {len(glyphs)}")

    # for c in range(GRID_DIMS[0]):
    #     l_list = set()
    #     one_list = set()
    #     for p in pages[1:]:
    #         for y in range(0, GRID_DIMS[1]):
    #             g = p.get_glyph_at(c, y)
    #             if glyphs[g] == 'l':
    #                 l_list.add(g)
    #             elif glyphs[g] == '1':
    #                 one_list.add(g)
    #     print(f"Column {c}:\tl={[g.get_id() for g in l_list]}, 1={[g.get_id() for g in one_list]}")

    if OUTPUT is not None:
        print("Writing outputs...")
        wrote_files = []
        contents = [P0_CODE]
        for g in ordered_glyphs:
            contents.append(glyphs[g])

        full_text = "".join(contents).rstrip()
        full_text = re.sub(r'\s*--.*--', '', full_text)  # rm dangling extra stuff
        width = 76
        out_txt_file = f'{OUTPUT}/output.txt'
        with open(out_txt_file, 'w') as f:
            for i in range(len(full_text) // width + 1):
                line = full_text[i * width:min((i + 1) * width, len(full_text))] + "\n"
                f.write(line)
            wrote_files.append(out_txt_file)

        decoded = base64.b64decode(full_text)
        out_pdf_file = f'{OUTPUT}/DBC12 One Page Invite with Reply.pdf'
        with open(out_pdf_file, 'wb') as output_file:
            output_file.write(decoded)
            wrote_files.append(out_pdf_file)
        print(f"Done. Wrote: {wrote_files}")

    render_info = False
    cur_page = 1

    bg_color = pygame.Color(92, 64, 92)
    screen = pygame.display.set_mode((640, 480), pygame.RESIZABLE)
    pygame.display.set_caption("OCR")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Lucida Console", 24)

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                raise SystemExit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    raise SystemExit()
                elif e.key == pygame.K_RIGHT:
                    cur_page += 1
                elif e.key == pygame.K_LEFT:
                    cur_page -= 1
                elif e.key == pygame.K_SPACE:
                    render_info = not render_info

        screen.fill(bg_color)

        # loop the animation 1.5 times per second
        elapsed_time_ms = pygame.time.get_ticks()
        i = elapsed_time_ms // 100

        scr_w, scr_h = screen.get_size()

        if render_info:
            for idx, g in enumerate(sorted(glyphs.keys(), key=lambda k: glyphs[k])):
                x = idx % 12
                y = idx // 12
                screen.blit(pygame.transform.scale_by(g.raw, 2), (x * 16, y * 30))

                if g.vector in mappings:
                    char = font.render(mappings[g.vector], False, (0, 0, 0))
                    screen.blit(char, (x * 16 + 230, y * 30))

            wrap = 25
            for idx, char in enumerate(sorted(list(flipped_glyphs.keys()))):
                y = (idx % wrap) * 30
                x = 450 + (idx // wrap) * 128
                label = font.render(char + ":", False, 'white')
                screen.blit(label, (x, y))

                for idx2, g in enumerate(flipped_glyphs[char]):
                    screen.blit(pygame.transform.scale_by(g.raw, 2), (x + 32 + idx2 * 16, y))

            x = 850
            for idx, l_glyph in enumerate(flipped_glyphs['l']):
                y = idx * 30
                label = font.render("(L) " + str(l_glyph.get_id()) + ":", False, 'white')
                screen.blit(label, (x, y))
                screen.blit(pygame.transform.scale_by(l_glyph.raw, 2), (x + 128, y))
            for idx, one_glyph in enumerate(flipped_glyphs['1']):
                y = 30 * len(flipped_glyphs['l']) + idx * 30
                label = font.render("(1) " + str(one_glyph.get_id()) + ":", False, 'white')
                screen.blit(label, (x, y))
                screen.blit(pygame.transform.scale_by(one_glyph.raw, 2), (x + 128, y))

        else:
            page = pages[cur_page % N]
            screen.blit(page.raw, (0, 0))

            highlight1 = pygame.Surface((8, 15), pygame.SRCALPHA)
            highlight1.fill("yellow")
            highlight1.set_alpha(128)

            highlight2 = pygame.Surface((8, 15), pygame.SRCALPHA)
            highlight2.fill("orange")
            highlight2.set_alpha(128)

            for g in page.all_glyphs():
                if g not in glyphs:
                    continue
                elif glyphs[g] == "l":
                    screen.blit(highlight1, page.get_grid_rect(*g.xy))
                elif glyphs[g] == "1":
                    screen.blit(highlight2, page.get_grid_rect(*g.xy))

        pygame.display.flip()
        clock.tick(60)
