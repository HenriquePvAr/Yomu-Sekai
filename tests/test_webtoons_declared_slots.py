"""Webtoons pages resolve from data-url + declared size, without scrolling the reader.

Every page tag carries its real URL in data-url and its size in width/height; only
the transparent placeholder in src waits for the viewport. Scrolling the whole
reader to load each one took ~1 s per page (87 s for a 111-image episode).
"""
import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

import json
import shutil
import subprocess
import unittest

from yomu.download import webtoons_reader_bridge as bridge

_HARNESS = r"""
const images = [
  {attrs: {src: "https://webtoon-phinf.pstatic.net/a/p1.jpg", "data-url": "https://webtoon-phinf.pstatic.net/a/p1.jpg", width: "690", height: "1280.0"}, naturalWidth: 690, naturalHeight: 1280},
  {attrs: {src: "https://ic.pstatic.net/image/bg_transparency.png", "data-url": "https://webtoon-phinf.pstatic.net/a/p2.jpg", width: "690", height: "765.0"}, naturalWidth: 1, naturalHeight: 1},
  {attrs: {src: "https://ic.pstatic.net/image/bg_transparency.png"}, naturalWidth: 1, naturalHeight: 1},
].map(spec => ({...spec, currentSrc: "", className: "_images", id: "", alt: "",
  getAttribute: name => spec.attrs[name] ?? null, getBoundingClientRect: () => ({top: 0, width: 690, height: 10})}));
globalThis.window = {scrollY: 0};
globalThis.document = {baseURI: "https://www.webtoons.com/", querySelector: () => ({id: "_imageList", className: "", querySelectorAll: () => images})};
const run = new Function(SCRIPT);
console.log(JSON.stringify(run.call(null, "#_imageList", "img")));
"""


@unittest.skipUnless(shutil.which("node"), "node not installed")
class DeclaredSlotTests(unittest.TestCase):
    def test_placeholder_with_declared_page_resolves_and_bare_placeholder_waits(self):
        script = "const arguments = [\"#_imageList\", \"img\"];\n" + bridge._READ_SLOTS_SCRIPT
        code = _HARNESS.replace("SCRIPT", json.dumps(script))
        output = subprocess.run(["node", "-e", code], capture_output=True, text=True, check=True).stdout
        slots = json.loads(output)["slots"]
        self.assertEqual(slots[1]["url"], "https://webtoon-phinf.pstatic.net/a/p2.jpg")
        self.assertEqual((slots[1]["naturalWidth"], slots[1]["naturalHeight"]), (690, 765))
        self.assertEqual(slots[1]["source"], "data-url-declared")
        # Loaded pages are reported as before; a placeholder without data-url stays pending.
        self.assertEqual(slots[0]["naturalWidth"], 690)
        self.assertEqual(slots[2]["naturalWidth"], 1)


if __name__ == "__main__":
    unittest.main()
