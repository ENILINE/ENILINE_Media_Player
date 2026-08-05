"""QSlider that jumps the thumb to the click position instead of a page step."""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractSlider, QSlider, QStyle, QStyleOptionSlider


class JumpSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.orientation() == Qt.Horizontal:
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            handle = self.style().subControlRect(
                QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self
            )
            on_handle = handle.contains(event.pos())
            if not on_handle:
                groove = self.style().subControlRect(
                    QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self
                )
                span = groove.width() - handle.width()
                if span > 0:
                    pos = event.pos().x() - handle.width() // 2 - groove.left()
                    value = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), pos, span)
                    self.setValue(value)
            super().mousePressEvent(event)
            if not on_handle:
                # super() may start a groove page-step repeat timer; cancel it.
                self.setRepeatAction(QAbstractSlider.SliderNoAction)
        else:
            super().mousePressEvent(event)