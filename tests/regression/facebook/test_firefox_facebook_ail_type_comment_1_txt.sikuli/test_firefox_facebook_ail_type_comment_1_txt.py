# if you are putting your test script folders under {git project folder}/tests/, it will work fine.
# otherwise, you either add it to system path before you run or hard coded it in here.

INPUT_LIB_PATH = sys.argv[1]
sys.path.append(INPUT_LIB_PATH)

import os
import common
import basecase
import facebook

import shutil
import browser
import time


class Case(basecase.SikuliInputLatencyCase):

    def run(self):
        # Disable Sikuli action and info log
        com = common.General()
        com.infolog_enable(0)

        ff = browser.Firefox()
        fb = facebook.facebook()

        ff.clickBar()
        ff.enterLink(self.INPUT_TEST_TARGET)
        fb.wait_for_loaded()

        sleep(2)
        setAutoWaitTimeout(10)
        fb.focus_comment_box()

        sample1_fp = os.path.join(self.INPUT_IMG_SAMPLE_DIR_PATH, self.INPUT_IMG_OUTPUT_SAMPLE_1_NAME)

        sleep(2)
        capture_width = int(self.INPUT_RECORD_WIDTH)
        capture_height = int(self.INPUT_RECORD_HEIGHT)

        t1 = time.time()
        capimg2 = capture(0, 0, capture_width, capture_height)

        com.system_print('[log]  TYPE "a"')
        type("a")
        sleep(1)
        t2 = time.time()
        com.updateJson({'t1': t1, 't2': t2}, self.INPUT_TIMESTAMP_FILE_PATH)
        shutil.move(capimg2, sample1_fp.replace(os.path.splitext(sample1_fp)[1], '.png'))


case = Case(sys.argv)
case.run()
