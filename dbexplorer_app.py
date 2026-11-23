#!/usr/bin/env python3
"""
DB Explorer (Desktop) — โปรแกรมหน้าต่างสำหรับสำรวจฐานข้อมูล SQLite เช่น Priconne Master Database
ต้องการ:  Python 3.9+  และ  pip install PySide6
รัน:      python dbexplorer_app.py [ไฟล์.db]      (หรือลากไฟล์ .db มาวางบนหน้าต่าง)
เปิดไฟล์แบบอ่านอย่างเดียวเสมอ — ไม่แก้ไขข้อมูลต้นฉบับ
"""
import csv, os, re, sqlite3, sys, time
from urllib.parse import quote

from PySide6.QtCore import (QAbstractTableModel, QModelIndex, QPoint, QRect, QSettings, QSize, Qt, QUrl,
                            QThread, QTimer, Signal)
from PySide6.QtGui import (QAction, QColor, QFont, QKeySequence, QShortcut, QSyntaxHighlighter,
                           QTextCharFormat, QGuiApplication, QIcon)
from PySide6.QtWidgets import (QListWidgetItem, QAbstractItemView, QApplication, QCheckBox, QComboBox, QDialog, QDockWidget,
                               QFileDialog, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
                               QListWidget, QMainWindow, QMenu, QMessageBox, QPlainTextEdit, QPushButton,
                               QScrollArea, QSizePolicy, QSplitter, QTableView, QTableWidget, QTableWidgetItem, QTabWidget,
                               QToolButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

APP = "DB Explorer"
FIXED = 4  # จำนวนแท็บประจำ
MAX_SQL_ROWS = 5000
LANG = "th"          # "th" | "en"  — สลับได้จากปุ่ม 🌐 บนแถบด้านบน (จำค่าไว้ใน QSettings)
_WINDOWS = []        # เก็บหน้าต่างเก่าไว้ไม่ให้ถูกเก็บกวาดขณะ thread ยังทำงาน


def tt(th, en):
    return th if LANG == "th" else en

# ----------------------------------------------------------------------------- theme
THEMES = {
    "dark": dict(bg="#0a0c14", bg2="#0f1220", panel="#141828", panel2="#1a1f33", ink="#e9ecf8", mute="#8890ad",
                 line="#262c45", acc="#8b6cff", acc2="#ff5fa2", accbg="#232049", zero="#4d5476", num="#8fd3ff",
                 alt="#171c2f", sel="#2b2760"),
    "light": dict(bg="#f2f3fa", bg2="#ffffff", panel="#ffffff", panel2="#f3f4fb", ink="#1b1f33", mute="#6a7190",
                  line="#dfe2f0", acc="#6a4cf0", acc2="#e8458a", accbg="#e9e5ff", zero="#b3b8d0", num="#1769b5",
                  alt="#f7f8fd", sel="#dcd5ff"),
}
QSS = """
* {{ font-family: "Segoe UI","Noto Sans Thai","Noto Sans JP","Inter",sans-serif; font-size: 13px; color: {ink}; }}
QMainWindow, QDialog {{ background: {bg}; }}
QWidget#root {{ background: {bg}; }}
QAbstractItemView {{ background: {panel}; color: {ink}; selection-background-color: {accbg}; selection-color: {ink}; outline: 0; }}
QToolTip {{ background: {panel2}; color: {ink}; border: 1px solid {line}; padding: 4px; }}
QLabel {{ background: transparent; }}
QLabel#mute, QLabel[mute="true"] {{ color: {mute}; }}
QLabel#h1 {{ font-size: 24px; font-weight: 700; }}
QLabel#logo {{ font-size: 17px; font-weight: 800; color: {acc2}; }}
QLabel#statv {{ font-size: 22px; font-weight: 700; color: {acc}; }}
QFrame#hero {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {accbg}, stop:1 {panel}); border: 1px solid {line}; border-radius: 16px; }}
QFrame#stat {{ background: {bg2}; border: 1px solid {line}; border-radius: 12px; }}
QFrame#bar {{ background: {panel}; border-bottom: 1px solid {line}; }}
QLineEdit, QComboBox, QPlainTextEdit {{ background: {bg2}; border: 1px solid {line}; border-radius: 8px; padding: 5px 9px; selection-background-color: {acc}; placeholder-text-color: {mute}; }}
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {{ border: 1px solid {acc}; }}
QComboBox::drop-down {{ border: 0; width: 20px; }}
QComboBox QAbstractItemView {{ background: {panel}; border: 1px solid {line}; selection-background-color: {accbg}; }}
QPushButton, QToolButton {{ background: {panel2}; border: 1px solid {line}; border-radius: 8px; padding: 6px 13px; }}
QPushButton:hover, QToolButton:hover {{ border-color: {acc}; }}
QPushButton:pressed {{ background: {accbg}; }}
QPushButton#pri {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {acc}, stop:1 {acc2}); border: 0; color: white; font-weight: 600; padding: 7px 16px; }}
QPushButton#card {{ text-align: left; padding: 14px 16px; border-radius: 14px; background: {panel}; min-height: 44px; }}
QPushButton#card:hover {{ border-color: {acc}; background: {accbg}; }}
QPushButton#pill {{ border-radius: 14px; padding: 4px 12px; background: {panel}; }}
QPushButton#pill:hover {{ border-color: {acc2}; }}
QCheckBox {{ spacing: 6px; color: {mute}; }}
QCheckBox::indicator {{ width: 15px; height: 15px; border-radius: 4px; border: 1px solid {line}; background: {bg2}; }}
QCheckBox::indicator:checked {{ background: {acc}; border-color: {acc}; }}
QListWidget::indicator {{ width: 15px; height: 15px; border-radius: 4px; border: 1px solid {line}; background: {bg2}; }}
QListWidget::indicator:checked {{ background: {acc}; border-color: {acc}; }}
QTabWidget::pane {{ border: 0; }}
QTabBar {{ background: transparent; }}
QTabBar::tab {{ background: transparent; color: {mute}; padding: 8px 16px; margin: 6px 2px 0 2px; border-radius: 15px; border: 1px solid transparent; }}
QTabBar::tab:hover {{ color: {ink}; }}
QTabBar::tab:selected {{ background: {accbg}; color: {ink}; border: 1px solid {acc}; }}
QTabBar::close-button {{ subcontrol-position: right; margin-left: 4px; }}
QTreeWidget {{ background: transparent; border: 0; outline: 0; }}
QTreeWidget::item {{ padding: 4px 2px; border-radius: 7px; }}
QTreeWidget::item:hover {{ background: {panel2}; }}
QTreeWidget::item:selected {{ background: {accbg}; color: {ink}; }}
QTableView, QTableWidget {{ background: {panel}; alternate-background-color: {alt}; border: 1px solid {line}; border-radius: 12px; gridline-color: transparent;
    selection-background-color: {sel}; selection-color: {ink}; outline: 0; }}
QTableView::item {{ padding: 2px 6px; border-bottom: 1px solid {line}; }}
QHeaderView {{ background: {panel2}; }}
QHeaderView::section {{ background: {panel2}; color: {ink}; font-weight: 600; padding: 6px 8px; border: 0; border-right: 1px solid {line}; border-bottom: 1px solid {line}; }}
QHeaderView::section:hover {{ color: {acc2}; }}
QTableCornerButton::section {{ background: {panel2}; border: 0; }}
QHeaderView QLineEdit {{ padding: 2px 6px; font-size: 12px; border-radius: 6px; }}
QScrollBar:vertical {{ background: transparent; width: 12px; margin: 2px; }}
QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 2px; }}
QScrollBar::handle {{ background: {line}; border-radius: 4px; min-height: 30px; min-width: 30px; }}
QScrollBar::handle:hover {{ background: {zero}; }}
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{ background: none; border: 0; height: 0; width: 0; }}
QDockWidget {{ titlebar-close-icon: none; font-weight: 600; }}
QDockWidget::title {{ background: {panel2}; padding: 8px 12px; border-bottom: 1px solid {line}; }}
QMenu {{ background: {panel}; border: 1px solid {line}; border-radius: 8px; padding: 4px; }}
QMenu::item {{ padding: 6px 22px; border-radius: 6px; }}
QMenu::item:selected {{ background: {accbg}; }}
QListWidget {{ background: {panel}; border: 0; outline: 0; }}
QListWidget::item {{ padding: 8px 14px; }}
QListWidget::item:selected {{ background: {accbg}; border-left: 3px solid {acc}; }}
QStatusBar {{ background: {panel}; color: {mute}; border-top: 1px solid {line}; }}
QSplitter::handle {{ background: {line}; width: 1px; }}
QScrollArea {{ border: 0; background: transparent; }}
"""


def q(name):
    return '"' + str(name).replace('"', '""') + '"'


def like_arg(s):
    return "%" + s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


# ----------------------------------------------------------------------------- database layer
class DB:
    def __init__(self):
        self.path = None
        self.tables = []
        self.colmap = {}
        self.names = {}
        self.size = 0

    def connect(self):
        uri = "file:" + quote(os.path.abspath(self.path).replace("\\", "/")) + "?mode=ro"
        c = sqlite3.connect(uri, uri=True, check_same_thread=False)
        c.text_factory = lambda b: b.decode("utf-8", "replace")
        c.execute("PRAGMA query_only=ON")
        return c

    def load(self, path):
        if not os.path.isfile(path):
            raise ValueError(tt("ไม่พบไฟล์: ", "File not found: ") + path)
        old = self.path
        self.path = path
        try:
            c = self.connect()
            objs = c.execute("select name,type from sqlite_master where type in ('table','view') "
                             "and name not like 'sqlite_%' order by name").fetchall()
        except sqlite3.DatabaseError as e:
            self.path = old
            raise ValueError(tt("ไม่ใช่ไฟล์ SQLite ที่อ่านได้\n%s", "Not a readable SQLite file\n%s") % e)
        tables, colmap = [], {}
        for n, t in objs:
            cols = [r[1] for r in c.execute("pragma table_info(%s)" % q(n))]
            try:
                rows = c.execute("select count(*) from %s" % q(n)).fetchone()[0]
            except sqlite3.Error:
                rows = -1
            tables.append(dict(name=n, type=t, rows=rows, cols=len(cols)))
            for col in cols:
                colmap.setdefault(col, []).append(n)
        self.tables, self.colmap, self.size = tables, colmap, os.path.getsize(path)
        self.names = {}
        try:
            self.names = {r[0]: r[1] for r in c.execute("select unit_id,unit_name from unit_profile")}
        except sqlite3.Error:
            pass
        c.close()

    def columns(self, c, name):
        info = c.execute("pragma table_info(%s)" % q(name)).fetchall()
        return [r[1] for r in info]

    @staticmethod
    def where(cols, filters, search):
        parts, args = [], []
        for col, txt in (filters or {}).items():
            t = (txt or "").strip()
            if col not in cols or not t:
                continue
            if t.lower() == "null":
                parts.append("%s IS NULL" % q(col)); continue
            for op in (">=", "<=", "!=", "<>", "=", ">", "<"):
                if t.startswith(op):
                    v = t[len(op):].strip()
                    try:
                        v = float(v) if "." in v else int(v)
                    except ValueError:
                        pass
                    parts.append("%s %s ?" % (q(col), "!=" if op == "<>" else op)); args.append(v)
                    break
            else:
                parts.append("CAST(%s AS TEXT) LIKE ? ESCAPE '\\'" % q(col)); args.append(like_arg(t))
        if search:
            parts.append("(" + " OR ".join("CAST(%s AS TEXT) LIKE ? ESCAPE '\\'" % q(c) for c in cols) + ")")
            args += [like_arg(search)] * len(cols)
        return (" WHERE " + " AND ".join(parts)) if parts else "", args

    def page(self, name, filters, search, sort, desc, off, lim):
        c = self.connect()
        try:
            cols = self.columns(c, name)
            w, a = self.where(cols, filters, search)
            order = (" ORDER BY %s %s" % (q(sort), "DESC" if desc else "ASC")) if sort in cols else ""
            total = c.execute("select count(*) from %s%s" % (q(name), w), a).fetchone()[0]
            rows = c.execute("select * from %s%s%s limit ? offset ?" % (q(name), w, order), a + [lim, off]).fetchall()
            return cols, rows, total
        finally:
            c.close()

    def export(self, name, filters, search, sort, desc, path):
        c = self.connect()
        try:
            cols = self.columns(c, name)
            w, a = self.where(cols, filters, search)
            order = (" ORDER BY %s %s" % (q(sort), "DESC" if desc else "ASC")) if sort in cols else ""
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                wr = csv.writer(f); wr.writerow(cols)
                for r in c.execute("select * from %s%s%s" % (q(name), w, order), a):
                    wr.writerow([v.hex() if isinstance(v, bytes) else v for v in r])
        finally:
            c.close()

    def schema(self, name):
        c = self.connect()
        try:
            cols = c.execute("pragma table_info(%s)" % q(name)).fetchall()
            idx = []
            for r in c.execute("pragma index_list(%s)" % q(name)).fetchall():
                idx.append((r[1], r[2], [x[2] for x in c.execute("pragma index_info(%s)" % q(r[1]))]))
            sql = c.execute("select sql from sqlite_master where name=?", (name,)).fetchone()
            return cols, idx, (sql[0] if sql else "")
        finally:
            c.close()

    def run_sql(self, sql):
        c = self.connect()
        try:
            t0 = time.time()
            cur = c.execute(sql.strip().rstrip(";"))
            cols = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchmany(MAX_SQL_ROWS + 1)
            return cols, rows[:MAX_SQL_ROWS], len(rows) > MAX_SQL_ROWS, int((time.time() - t0) * 1000)
        finally:
            c.close()

    def search_all(self, text):
        c = self.connect(); hits = []; t0 = time.time(); like = like_arg(text)
        try:
            for t in self.tables:
                if t["rows"] <= 0:
                    continue
                cols = self.columns(c, t["name"])
                cond = " OR ".join("CAST(%s AS TEXT) LIKE ? ESCAPE '\\'" % q(x) for x in cols)
                try:
                    n = c.execute("select count(*) from (select 1 from %s where %s limit 1000)" % (q(t["name"]), cond),
                                  [like] * len(cols)).fetchone()[0]
                except sqlite3.Error:
                    continue
                if n:
                    hits.append((t["name"], n))
            hits.sort(key=lambda x: -x[1])
            return hits, int((time.time() - t0) * 1000)
        finally:
            c.close()

    def char_map(self, uid):
        c = self.connect()
        def rows(sql, args=()):
            cur = c.execute(sql, args); cn = [x[0] for x in cur.description]
            return [dict(zip(cn, r)) for r in cur.fetchall()]
        try:
            d = {"uid": uid, "chara": uid // 100}
            ch = uid // 100
            d["unit"] = (rows("select * from unit_data where unit_id=?", (uid,)) or [{}])[0]
            d["profile"] = (rows("select * from unit_profile where unit_id=?", (uid,)) or [{}])[0]
            d["comments"] = rows("select * from unit_comments where unit_id between ? and ? order by unit_id,use_type,id", (ch * 100, ch * 100 + 99))
            d["room"] = rows("select * from room_unit_comments where unit_id between ? and ? order by unit_id,beloved_step,id", (ch * 100, ch * 100 + 99))
            try: d["album"] = rows("select * from album_voice_list where unit_id between ? and ? order by unit_id,id", (ch * 100, ch * 100 + 99))
            except sqlite3.Error: d["album"] = []
            d["story"] = rows("select story_id,title,sub_title,love_level,story_quest_id,unlock_quest_id from story_detail "
                              "where story_id between ? and ? order by story_id", (ch * 1000, ch * 1000 + 999))
            d["bonus"] = rows("select * from chara_story_status where story_id between ? and ? order by story_id", (ch * 1000, ch * 1000 + 999))
            d["atk"] = rows("select * from unit_attack_pattern where unit_id=?", (uid,))
            sk = (rows("select * from unit_skill_data where unit_id=?", (uid,)) or [{}])[0]
            skills = []
            for key, v in sk.items():
                if key != "unit_id" and v:
                    sd = (rows("select * from skill_data where skill_id=?", (v,)) or [{}])[0]
                    acts = []
                    for i in range(1, 21):
                        aid = sd.get("action_%d" % i)
                        if aid:
                            a = (rows("select * from skill_action where action_id=?", (aid,)) or [{"action_id": aid}])[0]
                            a["_dep"] = sd.get("depend_action_%d" % i, 0); a["_i"] = i; acts.append(a)
                    skills.append(dict(key=key, skill_id=v, data=sd, actions=acts))
            d["skills"] = skills
            try: d["override"] = rows("select * from unit_profile_display_override where unit_id=? order by unknown_1", (uid,))
            except sqlite3.Error: d["override"] = []
            try:
                d["ue"] = rows("select u.equip_slot, e.* from unit_unique_equipment u join unique_equipment_data e on e.equipment_id = u.equip_id "
                               "where u.unit_id=? order by u.equip_slot", (uid,))
            except sqlite3.Error: d["ue"] = []
            d["ue_sp"], d["ue_rate"], d["ue_items"] = [], [], {}
            ids = ",".join(str(int(e["equipment_id"])) for e in d["ue"])
            if ids:
                try:
                    d["ue_sp"] = rows("select * from ex_unique_equipment_1 where equipment_id in (%s)" % ids)
                    d["ue_rate"] = rows("select * from unique_equip_enhance_rate where equipment_id in (%s) order by equipment_id, min_lv" % ids)
                    it = ",".join(str(int(x["required_item_id"])) for x in d["ue_sp"]) or "0"
                    d["ue_items"] = {r["item_id"]: r["item_name"] for r in rows("select item_id, item_name from item_data where item_id in (%s)" % it)}
                except sqlite3.Error: pass
            rel = []
            for t in self.colmap.get("unit_id", []):
                n = c.execute("select count(*) from %s where unit_id=?" % q(t), (uid,)).fetchone()[0]
                if n: rel.append((t, n))
            d["related"] = rel
            return d
        finally:
            c.close()

    def refs(self, col, val):
        c = self.connect(); out = []
        try:
            for t in self.colmap.get(col, []):
                n = c.execute("select count(*) from %s where %s=?" % (q(t), q(col)), (val,)).fetchone()[0]
                if n:
                    out.append((t, n))
            return out
        finally:
            c.close()


class Task(QThread):
    done = Signal(object, object)

    def __init__(self, fn, parent=None):
        super().__init__(parent); self.fn = fn

    def run(self):
        try:
            self.done.emit(self.fn(), None)
        except Exception as e:  # noqa
            self.done.emit(None, str(e))


def NAME_COL(c):
    return bool(re.search(r"(^|_)unit_id$|^unit$", c))


# ----------------------------------------------------------------------------- model / widgets
class PageModel(QAbstractTableModel):
    def __init__(self, db, theme):
        super().__init__()
        self.db, self.theme = db, theme
        self.cols, self.rows, self.off = [], [], 0

    def setData_(self, cols, rows, off=0):
        self.beginResetModel(); self.cols, self.rows, self.off = cols, rows, off; self.endResetModel()

    def rowCount(self, p=QModelIndex()): return 0 if p.isValid() else len(self.rows)
    def columnCount(self, p=QModelIndex()): return 0 if p.isValid() else len(self.cols)

    def text(self, r, c):
        v = self.rows[r][c]
        if v is None: return "NULL"
        if isinstance(v, bytes): return "[BLOB %d B]" % len(v)
        s = str(v)
        if NAME_COL(self.cols[c]) and v in self.db.names: s += "  ·  " + self.db.names[v]
        return s

    def data(self, idx, role=Qt.DisplayRole):
        if not idx.isValid(): return None
        v = self.rows[idx.row()][idx.column()]
        if role == Qt.DisplayRole:
            t = self.text(idx.row(), idx.column())
            return t if len(t) < 300 else t[:300] + "…"
        if role == Qt.ToolTipRole:
            return None if v is None else self.text(idx.row(), idx.column())[:800]
        if role == Qt.ForegroundRole:
            if v is None or isinstance(v, bytes) or v == 0 and isinstance(v, (int, float)):
                return QColor(self.theme["zero"])
            if isinstance(v, (int, float)): return QColor(self.theme["num"])
        if role == Qt.TextAlignmentRole and isinstance(v, (int, float)):
            return int(Qt.AlignRight | Qt.AlignVCenter)
        if role == Qt.FontRole and v is None:
            f = QFont(); f.setItalic(True); return f
        return None

    def headerData(self, s, o, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self.cols[s] if o == Qt.Horizontal else str(self.off + s + 1)
        if role == Qt.TextAlignmentRole and o == Qt.Vertical:
            return int(Qt.AlignRight | Qt.AlignVCenter)
        return None


class FilterHeader(QHeaderView):
    changed = Signal()
    FH = 28

    def __init__(self, parent):
        super().__init__(Qt.Horizontal, parent)
        self.edits = []
        self.setSectionsClickable(True)
        self.setHighlightSections(False)
        self.setFixedHeight(34 + self.FH)
        self.setDefaultAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.sectionResized.connect(self.place)
        self.sectionMoved.connect(self.place)
        parent.horizontalScrollBar().valueChanged.connect(self.place)
        parent.horizontalScrollBar().rangeChanged.connect(self.place)

    def paintSection(self, painter, rect, i):
        r = QRect(rect); r.setHeight(max(10, rect.height() - self.FH))
        super().paintSection(painter, r, i)

    def setColumns(self, cols, values):
        for e in self.edits: e.deleteLater()
        self.edits = []
        for c in cols:
            e = QLineEdit(self); e.setPlaceholderText(tt("กรอง…", "Filter…")); e.setText(values.get(c, "")); e.setProperty("col", c)
            e.textChanged.connect(lambda *_: self.changed.emit()); e.show(); self.edits.append(e)
        self.place()

    def values(self):
        return {e.property("col"): e.text() for e in self.edits if e.text()}

    def place(self, *_):
        for i, e in enumerate(self.edits):
            if i >= self.count() or self.isSectionHidden(i):
                e.hide(); continue
            e.setGeometry(self.sectionViewportPosition(i) + 3, self.height() - self.FH + 2, max(20, self.sectionSize(i) - 7), self.FH - 5)
            e.show()

    def resizeEvent(self, ev):
        super().resizeEvent(ev); self.place()


class Grid(QTableView):
    def __init__(self):
        super().__init__()
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setWordWrap(False); self.setShowGrid(False)
        self.verticalHeader().setDefaultSectionSize(26)
        self.verticalHeader().setMinimumWidth(46)

    def keyPressEvent(self, e):
        if e.matches(QKeySequence.Copy):
            sel = self.selectionModel().selectedIndexes()
            if sel:
                m = self.model(); rows = sorted({i.row() for i in sel}); cols = sorted({i.column() for i in sel})
                chosen = {(i.row(), i.column()) for i in sel}
                lines = ["\t".join(m.text(r, c) if (r, c) in chosen else "" for c in cols) for r in rows]
                QGuiApplication.clipboard().setText("\n".join(lines))
            return
        super().keyPressEvent(e)


class SqlHighlighter(QSyntaxHighlighter):
    KW = ("select from where and or not in like limit offset order by group having join left right inner outer on as "
          "union all distinct count sum avg min max case when then else end null is between desc asc with exists cast "
          "pragma table_info").split()

    def __init__(self, doc, theme):
        super().__init__(doc)
        self.kw = QTextCharFormat(); self.kw.setForeground(QColor(theme["acc2"])); self.kw.setFontWeight(700)
        self.num = QTextCharFormat(); self.num.setForeground(QColor(theme["num"]))
        self.st = QTextCharFormat(); self.st.setForeground(QColor("#7ee0a1"))
        self.cm = QTextCharFormat(); self.cm.setForeground(QColor(theme["mute"]))
        self.rx = re.compile(r"\b(" + "|".join(self.KW) + r")\b", re.I)

    def highlightBlock(self, t):
        for m in self.rx.finditer(t): self.setFormat(m.start(), m.end() - m.start(), self.kw)
        for m in re.finditer(r"\b\d+(\.\d+)?\b", t): self.setFormat(m.start(), m.end() - m.start(), self.num)
        for m in re.finditer(r"'[^']*'", t): self.setFormat(m.start(), m.end() - m.start(), self.st)
        for m in re.finditer(r"--.*$", t): self.setFormat(m.start(), m.end() - m.start(), self.cm)


def lbl(text, name=None, mute=False):
    l = QLabel(text)
    if name: l.setObjectName(name)
    if mute: l.setProperty("mute", True)
    return l


# ----------------------------------------------------------------------------- tabs
class TableTab(QWidget):
    selected = Signal(list, list)  # cols, row

    def __init__(self, win, name):
        super().__init__()
        self.win, self.db, self.name = win, win.db, name
        self.sort, self.desc, self.off, self.total, self.seq = "", False, 0, 0, 0
        self.model = PageModel(self.db, win.theme)
        lay = QVBoxLayout(self); lay.setContentsMargins(14, 6, 14, 10); lay.setSpacing(8)

        tb = QHBoxLayout()
        self.search = QLineEdit(); self.search.setPlaceholderText(tt("🔍 ค้นหาในตารางนี้ (ทุกคอลัมน์)…", "🔍 Search this table (all columns)…")); self.search.setFixedWidth(280)
        self.hz = QCheckBox(tt("ซ่อนคอลัมน์ที่ว่าง/0", "Hide empty / 0 columns")); self.hz.toggled.connect(self.apply_hide)
        self.lim = QComboBox(); [self.lim.addItem(tt("%d แถว/หน้า", "%d rows/page") % n, n) for n in (50, 100, 250, 500, 1000)]; self.lim.setCurrentIndex(1)
        self.info = lbl("", mute=True)
        bc = QPushButton(tt("ล้างตัวกรอง", "Clear filters")); be = QPushButton(tt("⬇ ส่งออก CSV", "⬇ Export CSV"))
        tb.addWidget(self.search); tb.addWidget(self.hz); tb.addStretch(); tb.addWidget(self.info); tb.addWidget(self.lim); tb.addWidget(bc); tb.addWidget(be)
        lay.addLayout(tb)

        self.sub = QTabWidget(); lay.addWidget(self.sub, 1)
        self.grid = Grid(); self.grid.setModel(self.model)
        self.fh = FilterHeader(self.grid); self.grid.setHorizontalHeader(self.fh)
        self.sub.addTab(self.grid, tt("📋 ข้อมูล", "📋 Data"))
        self.schema = QTableWidget(); self.schema_box = QWidget()
        self.sub.addTab(self.schema_box, tt("🧩 โครงสร้าง", "🧩 Schema"))

        nav = QHBoxLayout()
        self.b1, self.b2, self.b3, self.b4 = [QPushButton(t) for t in ("«", "‹", "›", "»")]
        self.pg = lbl("", mute=True)
        for w in (self.b1, self.b2, self.pg, self.b3, self.b4): nav.addWidget(w)
        nav.addStretch(); nav.addWidget(lbl(tt("💡 ช่องกรอง: >100  =5  !=0  null · ดับเบิลคลิกแถวเพื่อดูรายละเอียด", "💡 Filter boxes: >100  =5  !=0  null · double-click a row for details"), mute=True))
        lay.addLayout(nav)

        self.timer = QTimer(self); self.timer.setSingleShot(True); self.timer.setInterval(350); self.timer.timeout.connect(self.reset_load)
        self.search.textChanged.connect(lambda: self.timer.start()); self.fh.changed.connect(lambda: self.timer.start())
        self.lim.currentIndexChanged.connect(self.reset_load)
        self.fh.sectionClicked.connect(self.on_sort)
        bc.clicked.connect(self.clear); be.clicked.connect(self.export)
        self.b1.clicked.connect(lambda: self.go(0)); self.b2.clicked.connect(lambda: self.go(self.off - self.limit()))
        self.b3.clicked.connect(lambda: self.go(self.off + self.limit())); self.b4.clicked.connect(lambda: self.go(10 ** 9))
        self.grid.doubleClicked.connect(lambda *_: self.win.show_detail())
        self.grid.selectionModel().currentRowChanged.connect(lambda *_: self.emit_sel())
        self._build_schema()
        self.filters_init = {}

    def limit(self): return self.lim.currentData()

    def set_filters(self, f, search=""):
        self.filters_init = f; self.search.blockSignals(True); self.search.setText(search); self.search.blockSignals(False)
        self.sort = ""; self.off = 0; self.load(rebuild=True)

    def reset_load(self): self.off = 0; self.load()

    def go(self, off):
        lim = self.limit(); last = max(0, (self.total - 1) // lim * lim)
        self.off = max(0, min(off, last)); self.load()

    def on_sort(self, i):
        c = self.model.cols[i]
        self.desc = (not self.desc) if self.sort == c else False; self.sort = c
        self.fh.setSortIndicatorShown(True); self.fh.setSortIndicator(i, Qt.DescendingOrder if self.desc else Qt.AscendingOrder)
        self.off = 0; self.load()

    def clear(self):
        self.search.blockSignals(True); self.search.clear(); self.search.blockSignals(False)
        for e in self.fh.edits: e.blockSignals(True); e.clear(); e.blockSignals(False)
        self.sort = ""; self.fh.setSortIndicatorShown(False); self.reset_load()

    def load(self, rebuild=False):
        self.seq += 1; my = self.seq
        filters = self.fh.values() if not rebuild else self.filters_init
        args = (self.name, filters, self.search.text(), self.sort, self.desc, self.off, self.limit())
        t = Task(lambda: self.db.page(*args), self); self.win.keep(t)
        t.done.connect(lambda res, err: self.loaded(my, res, err, rebuild)); t.start()

    def loaded(self, my, res, err, rebuild):
        if my != self.seq: return
        if err: self.info.setText("⚠ " + err); return
        cols, rows, total = res; self.total = total
        new_cols = cols != self.model.cols
        keep = self.fh.values()
        self.model.setData_(cols, rows, self.off)
        if new_cols or rebuild:
            self.fh.setColumns(cols, self.filters_init if rebuild else keep)
            if new_cols:
                for i in range(len(cols)): self.grid.setColumnWidth(i, 210 if NAME_COL(cols[i]) else min(220, max(90, len(cols[i]) * 9 + 36)))
        self.apply_hide(); self.fh.place()
        lim = self.limit(); a = self.off + 1 if total else 0; b = min(self.off + lim, total)
        self.info.setText(tt("%s–%s จาก %s แถว", "%s–%s of %s rows") % (f"{a:,}", f"{b:,}", f"{total:,}"))
        self.pg.setText(tt("  หน้า %d / %d  ", "  Page %d / %d  ") % (self.off // lim + 1, max(1, -(-total // lim))))
        self.win.status(tt("%s · %s แถว", "%s · %s rows") % (self.name, f"{total:,}"))

    def apply_hide(self, *_):
        hz = self.hz.isChecked()
        for i in range(len(self.model.cols)):
            empty = all(r[i] in (None, 0, "") for r in self.model.rows) and bool(self.model.rows)
            self.grid.setColumnHidden(i, hz and empty)
        self.fh.place()

    def emit_sel(self):
        r = self.grid.currentIndex().row()
        if 0 <= r < len(self.model.rows): self.selected.emit(self.model.cols, list(self.model.rows[r]))

    def export(self):
        p, _ = QFileDialog.getSaveFileName(self, tt("ส่งออก CSV", "Export CSV"), self.name + ".csv", "CSV (*.csv)")
        if not p: return
        f, s, so, d = self.fh.values(), self.search.text(), self.sort, self.desc
        t = Task(lambda: self.db.export(self.name, f, s, so, d, p), self); self.win.keep(t)
        t.done.connect(lambda r, e: self.win.status(tt("ส่งออกแล้ว: ", "Exported: ") + p) if not e else QMessageBox.warning(self, APP, e)); t.start()

    def _build_schema(self):
        lay = QVBoxLayout(self.schema_box); lay.setContentsMargins(0, 8, 0, 0)
        try:
            cols, idx, sql = self.db.schema(self.name)
        except Exception as e:
            lay.addWidget(lbl(str(e))); return
        t = QTableWidget(len(cols), 6)
        t.setHorizontalHeaderLabels(["#", tt("ชื่อคอลัมน์", "Column"), tt("ชนิด", "Type"), "PK", "NOT NULL", tt("ค่าเริ่มต้น", "Default")])
        for i, c in enumerate(cols):
            for j, v in enumerate([c[0], c[1], c[2], "🔑" if c[5] else "", "✓" if c[3] else "", "" if c[4] is None else c[4]]):
                t.setItem(i, j, QTableWidgetItem(str(v)))
        t.horizontalHeader().setStretchLastSection(True); t.setEditTriggers(QAbstractItemView.NoEditTriggers)
        t.verticalHeader().hide(); t.setAlternatingRowColors(True); t.setColumnWidth(1, 240); t.setColumnWidth(2, 110)
        lay.addWidget(t, 3)
        box = QPlainTextEdit(); box.setReadOnly(True); box.setFont(QFont("Consolas", 10))
        box.setPlainText(("Indexes\n" + "\n".join("%s%s (%s)" % ("UNIQUE " if u else "", n, ", ".join(c)) for n, u, c in idx) + "\n\n" if idx else "") + "CREATE statement\n" + sql)
        lay.addWidget(box, 2)
        b = QPushButton(tt("⚡ เปิดใน SQL", "⚡ Open in SQL")); b.clicked.connect(lambda: self.win.open_sql('SELECT *\nFROM "%s"\nLIMIT 100;' % self.name))
        lay.addWidget(b, 0, Qt.AlignLeft)


class SqlTab(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win; self.last = ""
        lay = QVBoxLayout(self); lay.setContentsMargins(14, 8, 14, 10); lay.setSpacing(8)
        self.ed = QPlainTextEdit(); self.ed.setFont(QFont("Consolas", 11)); self.ed.setFixedHeight(150)
        self.ed.setPlaceholderText(tt("SELECT * FROM unit_data LIMIT 10;      (Ctrl+Enter เพื่อรัน — อ่านอย่างเดียว ปลอดภัย)", "SELECT * FROM unit_data LIMIT 10;      (Ctrl+Enter to run — read-only, safe)"))
        self.hl = SqlHighlighter(self.ed.document(), win.theme)
        lay.addWidget(self.ed)
        r = QHBoxLayout(); run = QPushButton(tt("▶  รัน   Ctrl+Enter", "▶  Run   Ctrl+Enter")); run.setObjectName("pri")
        self.hist = QComboBox(); self.hist.setMinimumWidth(300); self.info = lbl("", mute=True); ex = QPushButton(tt("⬇ ส่งออก CSV", "⬇ Export CSV"))
        r.addWidget(run); r.addWidget(self.hist); r.addWidget(self.info, 1); r.addWidget(ex); lay.addLayout(r)
        self.model = PageModel(win.db, win.theme); self.grid = Grid(); self.grid.setModel(self.model); lay.addWidget(self.grid, 1)
        run.clicked.connect(self.run); ex.clicked.connect(self.export)
        QShortcut(QKeySequence("Ctrl+Return"), self.ed, activated=self.run); QShortcut(QKeySequence("Ctrl+Enter"), self.ed, activated=self.run)
        self.hist.activated.connect(lambda i: i > 0 and self.ed.setPlainText(self.win.hist[i - 1]))
        self.fill_hist()

    def fill_hist(self):
        self.hist.clear(); self.hist.addItem(tt("🕘 ประวัติคำสั่ง…", "🕘 Query history…"))
        for h in self.win.hist: self.hist.addItem(" ".join(h.split())[:80])

    def run(self):
        sql = self.ed.toPlainText()
        if not sql.strip() or not self.win.db.path: return
        self.info.setText(tt("กำลังรัน…", "Running…"))
        t = Task(lambda: self.win.db.run_sql(sql), self); self.win.keep(t)
        def done(res, err):
            if err: self.info.setText("⚠ " + err); self.info.setStyleSheet("color:#ff8497"); return
            self.info.setStyleSheet(""); cols, rows, trunc, ms = res; self.last = sql
            self.model.setData_(cols, rows)
            for i in range(len(cols)): self.grid.setColumnWidth(i, 140)
            self.info.setText(tt("%s แถว%s · %d ms", "%s rows%s · %d ms") % (f"{len(rows):,}", tt(" (ตัดที่ 5,000)", " (truncated at 5,000)") if trunc else "", ms))
            self.win.hist = [sql] + [h for h in self.win.hist if h != sql][:29]; self.win.s.setValue("hist", self.win.hist); self.fill_hist()
        t.done.connect(done); t.start()

    def export(self):
        if not self.model.rows and not self.model.cols: return
        p, _ = QFileDialog.getSaveFileName(self, tt("ส่งออก CSV", "Export CSV"), "query.csv", "CSV (*.csv)")
        if not p: return
        with open(p, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f); w.writerow(self.model.cols)
            for r in self.model.rows: w.writerow([v.hex() if isinstance(v, bytes) else v for v in r])
        self.win.status(tt("ส่งออกแล้ว: ", "Exported: ") + p)


class SearchTab(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        lay = QVBoxLayout(self); lay.setContentsMargins(14, 8, 14, 10); lay.setSpacing(8)
        r = QHBoxLayout(); self.ed = QLineEdit(); self.ed.setPlaceholderText(tt("🔎 พิมพ์ชื่อตัวละคร ข้อความ หรือรหัส เช่น Hiyori, 100101 …", "🔎 Type a character name, text or ID, e.g. Hiyori, 100101 …")); self.ed.setMinimumHeight(36)
        b = QPushButton(tt("ค้นหา", "Search")); b.setObjectName("pri"); self.info = lbl("", mute=True)
        r.addWidget(self.ed, 1); r.addWidget(b); lay.addLayout(r); lay.addWidget(self.info)
        self.res = QTableWidget(0, 2); self.res.setHorizontalHeaderLabels([tt("ตาราง", "Table"), tt("จำนวนแถวที่พบ", "Matching rows")])
        self.res.verticalHeader().hide(); self.res.horizontalHeader().setStretchLastSection(True); self.res.setColumnWidth(0, 420)
        self.res.setEditTriggers(QAbstractItemView.NoEditTriggers); self.res.setSelectionBehavior(QAbstractItemView.SelectRows); self.res.setAlternatingRowColors(True)
        lay.addWidget(self.res, 1)
        lay.addWidget(lbl(tt("ดับเบิลคลิกผลลัพธ์เพื่อเปิดตารางพร้อมค้นหาคำนั้น", "Double-click a result to open the table with that search applied"), mute=True))
        b.clicked.connect(self.go); self.ed.returnPressed.connect(self.go)
        self.res.cellDoubleClicked.connect(lambda r, c: self.win.open_table(self.res.item(r, 0).text(), search=self.ed.text()))

    def go(self):
        t_ = self.ed.text().strip()
        if not t_ or not self.win.db.path: return
        self.info.setText(tt("⏳ กำลังค้นหาทุกตาราง…", "⏳ Searching all tables…"))
        t = Task(lambda: self.win.db.search_all(t_), self); self.win.keep(t)
        def done(res, err):
            if err: self.info.setText("⚠ " + err); return
            hits, ms = res; self.info.setText(tt("พบใน %d ตาราง · %d ms", "Found in %d tables · %d ms") % (len(hits), ms)); self.res.setRowCount(len(hits))
            for i, (n, c) in enumerate(hits):
                self.res.setItem(i, 0, QTableWidgetItem(n)); it = QTableWidgetItem("1000+" if c >= 1000 else str(c)); self.res.setItem(i, 1, it)
        t.done.connect(done); t.start()


QUICK = [("unit_data", "👤", "ตัวละคร (สเตตัส)"), ("unit_profile", "📖", "โปรไฟล์ตัวละคร"), ("skill_data", "✨", "สกิล"),
         ("skill_action", "⚔️", "แอ็กชันสกิล"), ("enemy_parameter", "👹", "พารามิเตอร์ศัตรู"), ("quest_data", "🗺️", "เควสต์"),
         ("item_data", "🎒", "ไอเทม"), ("equipment_data", "🛡️", "อุปกรณ์"), ("gacha_data", "🎰", "กาชา"),
         ("unit_rarity", "⭐", "ความหายากตัวละคร"), ("clan_battle_period", "🏰", "Clan Battle"), ("shop_item", "🛒", "ร้านค้า")]


QUICK_EN = {"ตัวละคร (สเตตัส)": "Characters (stats)", "โปรไฟล์ตัวละคร": "Character profiles", "สกิล": "Skills", "แอ็กชันสกิล": "Skill actions",
            "พารามิเตอร์ศัตรู": "Enemy parameters", "เควสต์": "Quests", "ไอเทม": "Items", "อุปกรณ์": "Equipment", "กาชา": "Gacha",
            "ความหายากตัวละคร": "Unit rarity", "ร้านค้า": "Shop"}


class HomeTab(QScrollArea):
    def __init__(self, win):
        super().__init__(); self.win = win; self.setWidgetResizable(True)
        self.holder = QWidget(); self.holder.setObjectName("root"); self.setWidget(self.holder); self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.lay = QVBoxLayout(self.holder); self.lay.setContentsMargins(24, 14, 24, 24); self.lay.setSpacing(10)
        self.refresh()

    def clear(self):
        while self.lay.count():
            it = self.lay.takeAt(0)
            w = it.widget()
            if w: w.hide(); w.setParent(None); w.deleteLater()
            elif it.layout():
                l = it.layout()
                while l.count():
                    x = l.takeAt(0)
                    if x.widget(): x.widget().hide(); x.widget().setParent(None)

    def refresh(self):
        self.clear(); db = self.win.db
        if not db.path:
            self.lay.addStretch(1)
            for w in (lbl("🗄️", "h1"), lbl(tt("เปิดฐานข้อมูล SQLite", "Open an SQLite database"), "h1"), lbl(tt("กดปุ่มด้านล่าง หรือลากไฟล์ .db มาวางบนหน้าต่างนี้", "Click the button below, or drag a .db file onto this window"), mute=True)):
                w.setAlignment(Qt.AlignCenter); self.lay.addWidget(w)
            b = QPushButton(tt("📂  เลือกไฟล์…", "📂  Choose file…")); b.setObjectName("pri"); b.setFixedWidth(200); b.clicked.connect(self.win.open_dialog)
            self.lay.addWidget(b, 0, Qt.AlignCenter); self.lay.addStretch(2); return
        T = db.tables; tot = sum(max(0, t["rows"]) for t in T)
        hero = QFrame(); hero.setObjectName("hero"); h = QVBoxLayout(hero); h.setContentsMargins(26, 22, 26, 22)
        h.addWidget(lbl(tt("👋 ยินดีต้อนรับ", "👋 Welcome"), "h1")); h.addWidget(lbl(tt("สำรวจ %s — ดับเบิลคลิกตารางด้านซ้าย หรือกด Ctrl+K เพื่อกระโดดไปยังตารางที่ต้องการ", "Exploring %s — double-click a table on the left, or press Ctrl+K to jump to any table") % os.path.basename(db.path), mute=True))
        sr = QHBoxLayout()
        for v, k in ((f"{len(T):,}", tt("ตาราง", "Tables")), (f"{tot:,}", tt("แถวทั้งหมด", "Total rows")), (str(sum(1 for t in T if t["rows"] == 0)), tt("ตารางว่าง", "Empty tables")), ("%.1f MB" % (db.size / 1e6), tt("ขนาดไฟล์", "File size"))):
            f = QFrame(); f.setObjectName("stat"); fl = QVBoxLayout(f); fl.setContentsMargins(18, 8, 18, 8); fl.setSpacing(0)
            fl.addWidget(lbl(v, "statv")); fl.addWidget(lbl(k, mute=True)); sr.addWidget(f)
        sr.addStretch(); h.addLayout(sr)
        r = QHBoxLayout(); self.q = QLineEdit(); self.q.setPlaceholderText(tt("🔎 ค้นหาทุกตาราง เช่น Hiyori, 100101 …", "🔎 Search all tables, e.g. Hiyori, 100101 …")); self.q.setMinimumHeight(38); self.q.setMaximumWidth(560)
        go = QPushButton(tt("ค้นหา", "Search")); go.setObjectName("pri"); r.addWidget(self.q); r.addWidget(go); r.addStretch(); h.addLayout(r)
        go.clicked.connect(self.search); self.q.returnPressed.connect(self.search); self.lay.addWidget(hero)

        has = {t["name"] for t in T}
        def pills(title, names, counts=None):
            if not names: return
            self.lay.addSpacing(8); self.lay.addWidget(lbl(title, mute=True))
            g = QGridLayout(); g.setSpacing(8)
            for k, n in enumerate(names[:8]):
                b = QPushButton(n + ("   " + counts[n] if counts else "")); b.setObjectName("pill"); b.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
                b.clicked.connect(lambda _=0, n=n: self.win.open_table(n)); g.addWidget(b, k // 4, k % 4)
            for c in range(4): g.setColumnStretch(c, 1)
            self.lay.addLayout(g)
        pills(tt("⭐ ตารางโปรด", "⭐ Favorite tables"), [n for n in self.win.fav if n in has]); pills(tt("🕘 เปิดล่าสุด", "🕘 Recently opened"), [n for n in self.win.recent if n in has][:8])
        self.lay.addSpacing(8); self.lay.addWidget(lbl(tt("ทางลัด", "Shortcuts"), mute=True))
        g = QGridLayout(); g.setSpacing(10); k = 0
        cb = QPushButton(tt("🗺   แผนที่ตัวละคร\n      รวมข้อมูลทุกตารางของตัวละคร", "🗺   Character map\n      All tables for one character, in one page")); cb.setObjectName("card"); cb.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        cb.clicked.connect(lambda: self.win.tabs.setCurrentWidget(self.win.chartab)); g.addWidget(cb, 0, 0); k = 1
        for n, ic, label in QUICK:
            label = QUICK_EN.get(label, label) if LANG == "en" else label
            if n not in has: continue
            b = QPushButton("%s   %s\n      %s" % (ic, label, n)); b.setObjectName("card"); b.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred); b.clicked.connect(lambda _=0, n=n: self.win.open_table(n))
            g.addWidget(b, k // 4, k % 4); k += 1
        for c in range(4): g.setColumnStretch(c, 1)
        self.lay.addLayout(g)
        big = sorted(T, key=lambda t: -t["rows"])[:10]
        pills(tt("ตารางที่ใหญ่ที่สุด", "Largest tables"), [t["name"] for t in big], {t["name"]: f"{t['rows']:,}" for t in big})
        self.lay.addStretch(1)

    def search(self):
        if self.q.text().strip(): self.win.open_search(self.q.text().strip())



SKILL_ORDER = ["union_burst", "union_burst_evolution", "sp_union_burst"] + \
    ["main_skill_%d" % i for i in range(1, 11)] + ["main_skill_evolution_%d" % i for i in (1, 2)] + \
    ["main_skill_revolution_%d" % i for i in (1, 2)] + ["ex_skill_%d" % i for i in range(1, 6)] + \
    ["ex_skill_evolution_%d" % i for i in range(1, 6)] + ["sp_skill_%d" % i for i in range(1, 6)] + \
    ["sp_skill_evolution_%d" % i for i in (1, 2)] + ["sp_skill_revolution_%d" % i for i in (1, 2)]


def skill_label(k):
    m = {"union_burst": tt("UB (ยูเนียนเบิร์ส)", "UB (Union Burst)"), "union_burst_evolution": tt("UB+ (อีโวลูชัน)", "UB+ (Evolution)"), "sp_union_burst": "SP UB"}
    if k in m: return m[k]
    g = re.match(r"(main|ex|sp)_skill_(evolution_|revolution_)?(\d+)", k)
    if not g: return k
    base = {"main": tt("สกิล", "Skill"), "ex": tt("EX สกิล", "EX Skill"), "sp": tt("SP สกิล", "SP Skill")}[g.group(1)]
    suf = {"evolution_": tt("+ (อีโวลูชัน)", "+ (Evolution)"), "revolution_": tt("++ (รีโวลูชัน)", "++ (Revolution)"), None: ""}[g.group(2)]
    return "%s %s%s" % (base, g.group(3), suf)


def h(x):
    return ("" if x is None else str(x)).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\\n", "<br>").replace("\n", "<br>")


EN_HTML = {
    "ข้อมูลพื้นฐาน (unit_data)": "Basic info (unit_data)", "โปรไฟล์ (unit_profile)": "Profile (unit_profile)",
    "สกิลและความสามารถ (unit_skill_data → skill_data → skill_action)": "Skills & abilities (unit_skill_data → skill_data → skill_action)",
    "เนื้อเรื่อง (story_detail / chara_story_status)": "Story (story_detail / chara_story_status)",
    "คอมเมนต์/เสียงตัวละคร (unit_comments)": "Comments / voice lines (unit_comments)",
    "ตารางอื่นที่มีข้อมูลของ Unit ID นี้ (คลิกเพื่อเปิดพร้อมกรอง)": "Other tables containing this Unit ID (click to open filtered)",
    "ความหายากเริ่มต้น (rarity)": "Base rarity (rarity)", "ประเภทโจมตี (atk_type)": "Attack type (atk_type)", "1 (กายภาพ)": "1 (Physical)", "2 (เวท)": "2 (Magic)",
    "ตำแหน่ง (search_area_width)": "Position (search_area_width)", "ความเร็วเดิน (move_speed)": "Move speed (move_speed)",
    "เวลาโจมตีปกติ": "Normal attack cast time", "กิลด์ (guild_id)": "Guild (guild_id)", "เปิดตัว": "Release", "สิ้นสุด": "End",
    "ตัวละครจำกัด (is_limited)": "Limited unit (is_limited)", "เป็นคอลแลบ (is_collab)": "Collab (is_collab)",
    "ตัวต้นฉบับ (original_unit_id)": "Original unit (original_unit_id)",
    "CV (นักพากย์)": "CV (voice actor)", "หมู่เลือด": "Blood type", "วันเกิด (เดือน/วัน)": "Birthday (month/day)", "อายุ": "Age", "ส่วนสูง": "Height",
    "น้ำหนัก": "Weight", "เผ่าพันธุ์ (race)": "Race (race)", "งานอดิเรก/ชอบ (favorite)": "Hobbies / likes (favorite)", "กิลด์": "Guild",
    "แนะนำตัว (self_text)": "Self-intro (self_text)",
    "ลำดับการโจมตี": "Attack sequence", "วนซ้ำจากลำดับที่": "loops from step", " ถึง ": " to ",
    "(1 = โจมตีปกติ, ค่าอื่นคือสกิลตามลำดับ)": "(1 = normal attack, other values = skills in order)",
    "ไม่มีข้อมูลสกิล": "No skill data", "ไม่มีข้อมูล": "No data", "คำอธิบาย (JP)": "Description (JP)",
    "ไม่มีข้อมูลเนื้อเรื่องของตัวละครนี้ (เนื้อหาบทสนทนาเก็บในไฟล์ asset ของเกม ไม่ได้อยู่ในฐานข้อมูลนี้)":
        "No story data for this character (dialogue is stored in the game's asset files, not in this database)",
    "<td>ตอน</td>": "<td>Episode</td>", "ชื่อตอน": "Title", "ความสนิท": "Bond", "โบนัสสถานะ": "Stat bonus",
    "ตัวละครที่ได้รับโบนัสจากเนื้อเรื่องนี้ (chara_story_status)": "Characters receiving bonuses from this story (chara_story_status)",
}
_EN_KEYS = sorted(EN_HTML, key=len, reverse=True)


def tx(s):
    if LANG != "en": return s
    for k in _EN_KEYS: s = s.replace(k, EN_HTML[k])
    return s


# ----------------------------------------------------------------------------- game-data decoding (skill_action → human readable)
# ค่าเหล่านี้ถอดจากข้อความ JP ใน DB (คอลัมน์ description) + ตารางวิเคราะห์สกิล UB+ ของ Yui; ตัวที่ไม่ยืนยันแน่ใจมีเครื่องหมาย ?
STORY_STAT = {1: "HP", 2: "PATK", 3: "P.DEF", 4: "MATK", 5: "M.DEF", 6: "P.CRIT Rate", 7: "M.CRIT Rate", 8: "Dodge", 9: "Lifesteal",
              10: "HP Regen", 11: "TP Regen", 12: "P.Penetration", 13: "M.Penetration", 14: "TP Boost", 15: "HP Bonus", 16: "TP Reduce", 17: "Accuracy"}
UE_STAT = {"hp": "HP", "atk": "PATK", "magic_str": "MATK", "def": "P.DEF", "magic_def": "M.DEF", "physical_critical": "P.CRIT", "magic_critical": "M.CRIT",
           "physical_penetrate": "P.Pen", "magic_penetrate": "M.Pen", "accuracy": "Accuracy", "dodge": "Dodge", "life_steal": "Lifesteal",
           "wave_hp_recovery": "HP Regen", "wave_energy_recovery": "TP Regen", "hp_recovery_rate": "HP Bonus", "energy_recovery_rate": "TP Boost",
           "energy_reduce_rate": "TP Reduce"}
# action_detail_1 (type 10 / 38) = รหัสสถานะ*10 + (0 = เพิ่ม, 1 = ลด)      (th, en, เป็น %)
BUFF_STAT = {1: ("พลังโจมตีกายภาพ", "Physical attack power", False), 2: ("พลังป้องกันกายภาพ", "Physical defense power", False),
             3: ("พลังโจมตีเวท", "Magic attack power", False), 4: ("พลังป้องกันเวท", "Magic defense power", False),
             5: ("การหลบหลีก", "Dodge", False), 6: ("คริติคอลกายภาพ", "Physical critical", False), 7: ("คริติคอลเวท", "Magic critical", False),
             8: ("TP ที่ได้รับ (TP Boost)", "TP boost", False), 9: ("การดูดซับ HP", "HP absorption", False), 10: ("ความเร็วเคลื่อนที่", "Movement speed", False),
             11: ("ดาเมจคริติคอลกายภาพ", "Physical attack critical damage", True), 12: ("ดาเมจคริติคอลเวท", "Magic attack critical damage", True),
             13: ("ความแม่นยำ", "Accuracy", False), 14: ("ดาเมจคริติคอลที่ได้รับ", "critical damage taken", True),
             16: ("ดาเมจกายภาพที่ได้รับ", "physical damage taken", True), 17: ("ดาเมจเวทที่ได้รับ", "magic damage taken", True),
             18: ("ดาเมจกายภาพที่ทำได้", "physical damage dealt", True), 19: ("ดาเมจเวทที่ทำได้", "magic damage dealt", True),
             20: ("พลังบัฟ", "Buff potency", False), 21: ("พลังดีบัฟ", "Debuff potency", False)}
BARRIER = {1: ("บาเรียกันกายภาพ", "Physical Nullification Barrier"), 2: ("บาเรียกันเวท", "Magic Nullification Barrier"),
           3: ("บาเรียดูดซับกายภาพ", "Physical absorption barrier"), 4: ("บาเรียดูดซับเวท", "Magic absorption barrier"),
           5: ("บาเรียกันกายภาพ/เวท", "Physical/Magical Immunity Barrier"), 6: ("บาเรียดูดซับกายภาพ/เวท", "Physical/Magical absorption barrier")}
AILMENT = {3: ("อัมพาต", "Paralysis"), 4: ("แช่แข็ง", "Freeze"), 5: ("พันธนาการ", "Bind"), 6: ("หลับ", "Sleep"), 7: ("สตัน", "Stun"),
           8: ("กลายเป็นหิน", "Petrification"), 9: ("กักขัง", "Detain"), 10: ("สลบ", "Faint"), 14: ("สตัน (แยกช่อง)", "Stun (separate slot)")}
DOT = {1: ("พิษ", "Poison"), 2: ("แผลไหม้", "Burn"), 3: ("คำสาป", "Curse"), 4: ("พิษร้ายแรง", "Violent poison"), 5: ("คำสาปเพิ่มพลัง (呪詛)", "Hex (呪詛)")}
ACTION_NAME = {77: ("สถานะตอบสนองเหตุการณ์", "Reactive state"), 1: ("ดาเมจ", "Damage"), 2: ("เคลื่อนที่/ซ่อนตัว", "Move / stealth"), 3: ("กระเด็น/ดึงเข้า", "Knockback / pull"), 4: ("ฟื้นฟู HP", "HP recovery"),
               5: ("ชุบชีวิต?", "Revive?"), 6: ("บาเรีย", "Barrier"), 7: ("กำหนดเป้าหมายอ้างอิง", "Set reference target"), 8: ("สถานะผิดปกติ", "Status ailment"),
               9: ("ดาเมจต่อเนื่อง", "Damage over time"), 10: ("บัฟ/ดีบัฟ", "Stat buff / debuff"), 11: ("มึนงง/หลงเสน่ห์", "Charm / confusion"),
               12: ("มืดบอด", "Blind"), 13: ("ผนึกเสียง/UB", "Silence / UB seal"), 14: ("แปลงร่าง/บิน", "Transform / flight"), 15: ("อัญเชิญ", "Summon"),
               16: ("เปลี่ยน TP", "TP change"), 17: ("ทริกเกอร์", "Trigger"), 18: ("ชาร์จดาเมจ/เคาน์เตอร์", "Damage charge / counter"), 20: ("ยั่วยุ", "Taunt"),
               21: ("อมตะ/หลบหลีก", "Invulnerable / evade"), 22: ("เปลี่ยนรูปแบบโจมตี", "Change attack pattern"), 24: ("ชุบชีวิตตัวเอง", "Revive"),
               26: ("ส่งต่อค่าตัวคูณ", "Pass multiplier value"), 27: ("ส่งต่อค่าตัวคูณ (CHAIN)", "Pass multiplier value (CHAIN)"), 30: ("ทำลายตัวเอง/ยูนิตอัญเชิญ", "Self-destruct / destroy summons"),
               35: ("ให้ตราประทับ (刻印)", "Grant mark (刻印)"), 36: ("ฟิลด์ดาเมจต่อเนื่อง", "Damage field"), 37: ("ฟิลด์ฟื้นฟู HP", "HP recovery field"),
               38: ("ฟิลด์บัฟ/ดีบัฟ", "Stat field"), 46: ("ดาเมจตามสัดส่วน / ใช้ HP", "Percent damage / HP cost"), 47: ("ดาเมจพื้นที่", "Area damage"),
               48: ("ฟื้นฟูต่อวินาที", "Regeneration per second"), 49: ("ล้างสถานะ", "Dispel"), 52: ("เปลี่ยนระยะโจมตี", "Change attack range"),
               54: ("ล่องหน", "Stealth"), 59: ("ลดการฟื้นฟู HP", "HP recovery DOWN"), 61: ("ตื่นตระหนก", "Panic"), 71: ("ป้องกันตาย", "Death protection"),
               72: ("ลดดาเมจที่ได้รับ", "Damage cut"), 82: ("กันสถานะลดพลัง", "Debuff immunity"), 83: ("ความเร็วการกระทำ (บวกเพิ่ม)", "Action speed (additive)"),
               90: ("เพิ่มค่าสถานะ (ติดตัว)", "Passive stat UP"), 92: ("ยับยั้ง TP", "TP suppression"), 96: ("ฟิลด์ฟื้นฟู TP", "TP recovery field"),
               99: ("ฟิลด์ความเร็ว", "Action speed field"), 100: ("กันสถานะควบคุม", "CC immunity"), 112: ("ยืดเวลาโดนควบคุม", "CC duration extension"),
               116: ("จองหอง/ยึดติด", "Obsession")}
INFO_TYPES = {7, 17, 22, 26, 27, 35}
COND_NAME = {1900: ("เพิ่มเติม: เมื่อตัวเองมีบาเรียอยู่", "Activate additionally while a barrier is active on yourself."),
             1211: ("เมื่อใช้ครั้งแรก", "On first use"),
             1800: ("เมื่อเป้าหมายตรงหน้าเป็น Multi-target", "If the target in front is a multi-target"),
             741: ("เมื่อมีเพื่อนร่วมทีมที่พลังโจมตีกายภาพสูงกว่าตัวเอง", "I have a character with a higher physical attack power than me.")}
MARK_EN = {"スタミナ": "Stamina"}; MARK_TH = {"スタミナ": "สตามินา"}


def mark_label(desc):
    """ชื่อตัวนับ (刻印) จากคำอธิบาย JP เช่น 自分のスタミナを９消費する → [Stamina]"""
    m = re.search(r"自分の(.+?)(?:を|が)", desc or "")
    if not m: return None
    w = m.group(1)
    return "[%s]" % (MARK_EN.get(w, w) if LANG == "en" else MARK_TH.get(w, w))
_TGT = {2: ("สุ่ม", "Random"), 4: ("หลังสุด (ไกลสุด)", "Rearmost"), 8: ("สุ่ม", "Random"), 14: ("PATK สูงสุด", "Highest P.ATK"), 16: ("MATK สูงสุด", "Highest M.ATK"),
        5: ("HP ต่ำสุด", "Lowest HP"), 6: ("HP สูงสุด", "Highest HP"), 20: ("ตัวโจมตีกายภาพ", "Physical attackers"), 21: ("ตัวโจมตีเวท", "Magic attackers"),
        45: ("PDEF ต่ำสุด", "Lowest P.DEF"), 46: ("MDEF ต่ำสุด", "Lowest M.DEF")}


_COND_CACHE = {"mt": None, "data": {}}


def cond_override(t, code):
    """อ่านชื่อเงื่อนไขที่ผู้ใช้เขียนเองจาก condition_names.json (ข้างโปรแกรม) — คีย์ "28:741" หรือ "741" ; ค่าเป็นข้อความหรือ {"th":..,"en":..}"""
    import json
    for base in (os.path.dirname(os.path.abspath(__file__)), os.path.dirname(os.path.abspath(sys.executable)), os.getcwd()):
        f = os.path.join(base, "condition_names.json")
        if os.path.isfile(f):
            try:
                mt = os.path.getmtime(f)
                if _COND_CACHE["mt"] != (f, mt):
                    with open(f, encoding="utf-8") as fh: _COND_CACHE["data"] = json.load(fh)
                    _COND_CACHE["mt"] = (f, mt)
            except Exception: _COND_CACHE["data"] = {}
            break
    data = _COND_CACHE["data"]
    v = data.get("%s:%s" % (t, code), data.get(str(code)))
    if isinstance(v, dict): v = v.get(LANG) or v.get("en") or v.get("th")
    return v or None


def fmtn(x):
    try: x = float(x)
    except (TypeError, ValueError): return str(x)
    if x == int(x) and abs(x) < 1e15: return str(int(x))
    return ("%.10f" % x).rstrip("0") if abs(x) < 1e-3 else "%.6g" % x     # ไม่ใช้รูปแบบ 7.5e-06


def stat_effect(code):
    """รหัส action_detail_1 ของบัฟ/ดีบัฟ → (ชื่อ, เป็น %)"""
    if code in (1020, 1040):
        w = tt("กายภาพ", "Physical") if code == 1020 else tt("เวท", "Magic")
        return tt("ขีดล่างพลังป้องกัน%s (ไม่ถูกลด)", "%s defense lower limit (cannot be reduced)") % w, False
    sid, sign = divmod(code, 10); nm = BUFF_STAT.get(sid)
    if not nm: return tt("สถานะรหัส %d", "Stat code %d") % code, False
    st = tt(nm[0], nm[1])
    if sid in (14, 16, 17):      # "ที่ได้รับ": ลงท้าย 1 = ดีบัฟศัตรู → ได้รับเพิ่มขึ้น
        return (tt("%s เพิ่มขึ้น", "Increased %s") if sign == 1 else tt("%s ลดลง", "Decreased %s")) % st, nm[2]
    if sid in (18, 19):          # "ที่ทำได้"
        return (tt("%s เพิ่มขึ้น", "Increased %s") if sign == 0 else tt("%s ลดลง", "Decreased %s")) % st, nm[2]
    return (tt("%s เพิ่มขึ้น", "%s UP") if sign == 0 else tt("%s ลดลง", "%s DOWN")) % st, nm[2]


def target_text(a):
    asg, tp, cnt, rng = a.get("target_assignment") or 0, a.get("target_type") or 0, a.get("target_count") or 0, a.get("target_range") or 0
    if tp == 7: return tt("ตัวเอง", "Self")
    if asg == 0: return "—"
    if asg == 3: return tt("ทุกยูนิต (ทั้งสองฝ่าย)", "All units (both sides)")
    foe = asg == 1
    if tp == 3:
        if cnt == 99 and rng >= 2160: return tt("ศัตรูทั้งหมด", "All enemies") if foe else tt("พันธมิตรทั้งหมด", "All allies")
        if cnt == 99: return (tt("ศัตรูในรัศมี %d", "Enemies within %d") if foe else tt("พันธมิตรในรัศมี %d", "Allies within %d")) % rng
        if cnt == 1: return tt("ศัตรูตัวหน้าสุด", "Frontmost enemy") if foe else tt("พันธมิตรที่ใกล้สุด", "Nearest ally")
        return (tt("ศัตรูหน้าสุด %d ตัว", "Front %d enemies") if foe else tt("พันธมิตรที่ใกล้สุด %d คน", "Nearest %d allies")) % cnt
    if tp == 1:
        if cnt == 99: return (tt("ศัตรูรอบเป้าหมาย (รัศมี %d)", "Enemies around the target (r=%d)") if foe else tt("พันธมิตรในรัศมี %d", "Allies within %d")) % rng
        return tt("เป้าหมายเดิม (จากแอ็กชันก่อนหน้า)", "Same target as before")
    if tp == 34: return tt("พันธมิตรทั้งหมดยกเว้นตัวเอง", "All allies except self")
    if tp == 43: return tt("พันธมิตร PATK สูงสุด (ยกเว้นตัวเอง)", "Highest P.ATK ally (except self)")
    if tp == 18 and not foe: return tt("พันธมิตรที่ไกลสุด", "Farthest ally")
    if tp in _TGT:
        w = tt(*_TGT[tp])
        if cnt == 99: return (tt("ศัตรู: %s (ทั้งหมด)", "Enemies: %s (all)") if foe else tt("พันธมิตร: %s (ทั้งหมด)", "Allies: %s (all)")) % w
        return (tt("ศัตรู: %s", "Enemy: %s") if foe else tt("พันธมิตร: %s", "Ally: %s")) % w
    return (tt("ศัตรู (target type %d)", "Enemy (target type %d)") if foe else tt("พันธมิตร (target type %d)", "Ally (target type %d)")) % tp


def decode_action(a, marks=None):
    """แปลงแถว skill_action เป็น dict(kind, name, formula, dur, desc)  — รูปแบบเดียวกับตารางวิเคราะห์สกิลบนวิกิ"""
    t = a.get("action_type"); d1 = a.get("action_detail_1") or 0; d2 = a.get("action_detail_2") or 0; d3 = a.get("action_detail_3") or 0
    v = [(a.get("action_value_%d" % i) or 0) for i in range(1, 8)]
    sl = tt("เลเวลสกิล", "Skill Level")
    PA, MA = tt("พลังโจมตีกายภาพ", "Physical Attack Power"), tt("พลังโจมตีเวท", "Magic Attack Power")
    atk = {1: PA, 2: MA}
    r = dict(kind="effect", name="", formula="", dur=None, desc=a.get("description") or "")
    fd = lambda x: x      # แสดงตามค่าใน DB ตรงๆ (เช่น 12.5)

    def lin(base, per, coef=0, stat="", pct=False):
        u = "%" if pct else ""; s = ""
        if per and base == per: s = "(%s + 1) * %s%s" % (sl, fmtn(per), u)
        elif per and not base: s = "%s * %s%s" % (sl, fmtn(per), u)
        elif per and base > per: s = "(%s + 1) * %s%s + %s%s" % (sl, fmtn(per), u, fmtn(base - per), u)
        elif per: s = "%s%s + %s * %s%s" % (fmtn(base), u, sl, fmtn(per), u)
        elif base or not coef: s = fmtn(base) + u
        if coef: s = (s + " + " if s else "") + "%s * %s" % (stat, fmtn(coef))
        return s

    if t is None:
        r.update(kind="info", name=tt("(ไม่พบแอ็กชันใน DB)", "(action not found in DB)")); return r
    if t in (28, 45, 53, 23):
        ov = cond_override(t, d1)
        if ov: r.update(kind="cond", name=ov); return r
        if t == 28 and d1 // 1000 == 6:
            mk = (marks or {}).get(d1 - 6000) or mark_label(r["desc"]) or "[#%d]" % (d1 - 6000)
            base = tt("%s %s ขึ้นไป (ตัวเอง)", "%s %s or more (your own)") % (mk, fmtn(v[2]))
        else:
            nm = COND_NAME.get(d1) if t == 28 else {45: COND_NAME[1211], 53: ("ขณะฟิลด์ทำงานอยู่", "While the field is active")}.get(t)
            base = tt(*nm) if nm else {23: tt("ตรวจสถานะเป้าหมาย", "Check target state")}.get(t, tt("เงื่อนไข", "Condition"))
        r.update(kind="cond", name=base); return r
    if t == 1:
        r["name"] = {1: tt("ดาเมจกายภาพ", "Physical damage"), 2: tt("ดาเมจเวท", "Magic damage"), 3: tt("ดาเมจกายภาพ (ทะลุเกราะ)", "Physical damage (ignores DEF)")}.get(d1, tt("ดาเมจ", "Damage"))
        r["formula"] = lin(v[0], v[1], v[2], atk.get(d1, PA))
    elif t == 4:
        r["name"] = tt("ฟื้นฟู HP", "HP recovery"); r["formula"] = lin(v[1], v[2], v[3], atk.get(d1, PA))
    elif t == 6:
        r["name"] = tt(*BARRIER[d1]) if d1 in BARRIER else tt("บาเรีย (ชนิด %d)", "Barrier (kind %d)") % d1
        r["formula"] = lin(v[0], v[1]); r["dur"] = v[2] or None
    elif t == 8:
        if d1 == 2: r.update(name=tt("ความเร็วการกระทำ เพิ่มขึ้น", "Action speed UP"), formula="%s%%" % fmtn((v[0] - 1) * 100))
        elif d1 == 1: r.update(name=tt("ความเร็วการกระทำ ลดลง", "Action speed DOWN"), formula="%s%%" % fmtn(round((1 - v[0]) * 100, 4)))
        else: r["name"] = tt(*AILMENT[d1]) if d1 in AILMENT else tt("สถานะผิดปกติ (ชนิด %d)", "Status ailment (kind %d)") % d1
        r["dur"] = v[2] or None
    elif t == 9:
        r["name"] = tt(*DOT[d1]) if d1 in DOT else tt("ดาเมจต่อเนื่อง (ชนิด %d)", "Damage over time (kind %d)") % d1
        r["formula"] = lin(v[0], v[1]); r["dur"] = v[2] or None
    elif t in (10, 38):
        name, pct = stat_effect(d1)
        mode, base, per, dur = (v[0], v[1], v[2], v[3]) if t == 10 else (1, v[0], v[1], fd(v[2]))
        if mode == 2: f = tt("%s%% ของค่าเริ่มต้น", "%s%% of initial value") % fmtn(base)
        elif mode == 3: f = tt("%s%% ของค่าปัจจุบัน", "%s%% of current value") % fmtn(base)
        else: f = lin(base, per, pct=pct)
        if t == 38: name = tt("ฟิลด์: ", "Field: ") + name; f += tt(" (รัศมี %s)", " (radius %s)") % fmtn(v[4])
        r.update(name=name, formula=f, dur=dur or None)
    elif t == 16:
        r["name"] = {1: tt("ฟื้นฟู TP", "TP recovery"), 2: tt("ลด TP (ศัตรู)", "TP reduction (enemy)"), 4: tt("ฟื้นฟู TP (ค่าคงที่)", "TP recovery (fixed)")}.get(d1, tt("เปลี่ยน TP", "TP change"))
        r["formula"] = fmtn(v[0])
    elif t == 48:
        r["name"] = tt("ฟื้นฟู TP ต่อวินาที", "TP regeneration per second") if d1 == 1 else tt("ฟื้นฟู HP ต่อวินาที", "HP regeneration per second")
        r["formula"] = lin(v[0], v[1], v[2], tt("พลังโจมตี", "Attack Power")); r["dur"] = v[4] or None
    elif t == 72:
        nm = {1: (tt("ลดดาเมจกายภาพที่ได้รับ", "Physical damage cut"), True), 2: (tt("ลดดาเมจเวทที่ได้รับ", "Magic damage cut"), True),
              3: (tt("ลดดาเมจกายภาพ/เวทที่ได้รับ", "Physical/Magic damage cut"), True), 4: (tt("ลดดาเมจกายภาพ (ค่าคงที่)", "Physical damage reduction (flat)"), False),
              5: (tt("ลดดาเมจเวท (ค่าคงที่)", "Magic damage reduction (flat)"), False), 6: (tt("ลดดาเมจที่ได้รับ (ค่าคงที่)", "Damage reduction (flat)"), False)}.get(d1)
        if nm: r["name"], r["formula"] = nm[0], fmtn(v[0]) + ("%" if nm[1] else "")
        else: r["name"] = tt("ลดดาเมจ (ชนิด %d)", "Damage cut (kind %d)") % d1
        r["dur"] = v[2] or None
    elif t == 90:
        m = {2: 1, 3: 2, 4: 3, 5: 4, 6: 6, 7: 7}
        st = "HP" if d1 == 1 else (tt(BUFF_STAT[m[d1]][0], BUFF_STAT[m[d1]][1]) if d1 in m else None)
        r["name"] = (tt("%s เพิ่มขึ้น (ติดตัว)", "%s UP (passive)") % st) if st else tt("เพิ่มค่าสถานะ (ติดตัว) ชนิด %d", "Passive stat UP (kind %d)") % d1
        r["formula"] = lin(v[1], v[2])
    elif t == 36:
        r["name"] = tt("ฟิลด์ดาเมจ%s", "%s damage field") % (tt("กายภาพ", "Physical").lower() if LANG == "en" else tt("กายภาพ", "Physical")) if False else (tt("ฟิลด์ดาเมจกายภาพ", "Physical damage field") if d1 == 3 else tt("ฟิลด์ดาเมจเวท", "Magic damage field"))
        r["formula"] = lin(v[0], v[1], v[2], PA if d1 == 3 else MA); r["dur"] = fd(v[4]) or None
    elif t == 37:
        r["name"] = tt("ฟิลด์ฟื้นฟู HP", "HP recovery field"); r["formula"] = lin(v[0], v[1], v[2], tt("พลังโจมตี", "Attack Power")); r["dur"] = fd(v[4]) or None
    elif t == 96:
        r["name"] = tt("ฟิลด์ฟื้นฟู TP ต่อวินาที", "TP recovery field per second"); r["formula"] = fmtn(v[0]); r["dur"] = fd(v[2]) or None
    elif t == 99:
        r["name"] = tt("ฟิลด์ความเร็วการกระทำ", "Action speed field"); r["formula"] = "%s%%" % fmtn(round((v[0] - 1) * 100, 4)); r["dur"] = v[2] or None
    elif t == 83:
        r["name"] = tt("ความเร็วการกระทำ เพิ่มขึ้น", "Action speed UP") if d1 == 2 else tt("ความเร็วการกระทำ ลดลง (ซ้อนได้)", "Action speed DOWN (stackable)")
        r["formula"] = ("%s%% %s" % (fmtn(round(v[0] * 100, 4)), tt("(บวกเพิ่ม)", "(addition)"))) if d1 == 2 else "x%s" % fmtn(v[0]); r["dur"] = v[2] or None
    elif t == 35:
        lab = mark_label(r["desc"])
        if lab:
            amt = v[3]; mx = "最大" in r["desc"] and amt < 0
            r["name"] = lab
            r["formula"] = (tt("สูงสุด ", "Maximum ") if mx else "") + ("%+d" % amt if amt == int(amt) else "%+g" % amt) + (tt(" (ค่าสูงสุด %s)", " (Maximum value %s)") % fmtn(v[0]) if v[0] else "")
        else:
            r["kind"] = "info"; r["name"] = tt("ให้ตัวนับ/ตราประทับ #%s (刻印)", "Grant counter / mark #%s (刻印)") % fmtn(v[1])
            r["formula"] = "v1=%s, v3=%s, v4=%s" % (fmtn(v[0]), fmtn(v[2]), fmtn(v[3]))
    elif t == 77:
        lab = mark_label(r["desc"])
        if d1 in (1, 4) and lab and v[6]:
            r["name"] = tt("%s สถานะฟื้นฟู", "%s Recovery state") % lab
            r["formula"] = (tt("ทุกครั้งที่เพื่อนร่วมทีมใช้ Ultimate Burst, +%s", "Each time an ally activates their Ultimate Burst, +%s") if d1 == 4
                            else tt("ทุกครั้งที่ได้รับบัฟเพิ่มค่าสถานะ, +%s", "Each time it receives a stat-up effect, +%s")) % fmtn(v[6]); r["dur"] = v[4] or None
        else:
            r["name"] = tt(*ACTION_NAME[77]) if 77 in ACTION_NAME else tt("แอ็กชันชนิด %d", "Action type %d") % t
            r["formula"] = "d=(%s,%s,%s) " % (d1, d2, d3) + ", ".join("v%d=%s" % (i + 1, fmtn(x)) for i, x in enumerate(v) if x)
    elif t == 49:
        r["name"] = {10: tt("ลบบาเรียศัตรู", "Remove enemy barriers"), 1: tt("ล้างบัฟ", "Dispel buffs"), 2: tt("ล้างดีบัฟ", "Dispel debuffs")}.get(d1, tt("ล้างสถานะ (ชนิด %d)", "Dispel (kind %d)") % d1)
    elif t in (11, 12, 13, 20, 21):
        r["name"] = tt(*ACTION_NAME[t]); r["dur"] = v[0] or None
    else:
        nm = ACTION_NAME.get(t)
        r["name"] = tt(*nm) if nm else tt("แอ็กชันชนิด %d", "Action type %d") % t
        if t in INFO_TYPES: r["kind"] = "info"
        nz = ["v%d=%s" % (i + 1, fmtn(x)) for i, x in enumerate(v) if x]
        r["formula"] = ("d=(%s,%s,%s) " % (d1, d2, d3) if (d1 or d2 or d3) else "") + ", ".join(nz)
    return r


def skill_tag(key):
    """ป้ายสั้นของสกิล: UB, UB+, S1, S1+, S1++, EX1, EX1+ ..."""
    if key == "union_burst": return "UB"
    if key == "union_burst_evolution": return "UB+"
    if key == "sp_union_burst": return "SP UB"
    m = re.match(r"(main|ex|sp)_skill_(evolution_|revolution_)?(\d+)$", key)
    if not m: return key
    return "%s%s%s" % ({"main": "S", "ex": "EX", "sp": "SP"}[m.group(1)], m.group(3), {"evolution_": "+", "revolution_": "++", None: ""}[m.group(2)])


def fold_pass(a26, trow, marks):
    """type 26 (ส่งต่อตัวคูณ): บวก ตัวคูณ×ปริมาณ เข้ากับค่าของแอ็กชันเป้าหมาย (d1 = action_id, d2 = ลำดับค่าที่ถูกบวก)"""
    v = [(a26.get("action_value_%d" % i) or 0) for i in range(1, 8)]
    d2 = int(a26.get("action_detail_2") or 1); ta = trow["a"]
    base = ta.get("action_value_%d" % max(d2, 1)) or 0 if d2 == 1 else (ta.get("action_value_%d" % d2) or 0)
    coef, cap, src = v[1], v[3], int(v[0])
    if src >= 2000:
        mk = (marks or {}).get(src - 2000, "[#%d]" % (src - 2000))
        extra = "%s * %s %s" % (fmtn(coef), tt("การใช้", "Consumption"), mk)
        return (fmtn(base) + " + " + extra) if base else extra
    if src == 7:
        extra = "%s * %s%%" % (tt("พลังโจมตีกายภาพของเป้าหมาย", "Target's physical attack power"), fmtn(coef))
        s = ("%s + %s" % (fmtn(base), extra)) if base else extra
        if cap: s += "\n" + tt("สูงสุด %s%%", "up to a maximum of %s%%") % fmtn(base + cap)
        return s
    return "%s + %s * (value #%d)" % (trow["formula"], fmtn(coef), src)


def action_table_html(actions, T):
    mute, line, acc, acc2, panel2 = T["mute"], T["line"], T["acc"], T["acc2"], T["panel2"]
    marks = {}
    for a in actions:
        if a.get("action_type") == 35 and a.get("description"):
            lab = mark_label(a["description"])
            if lab: marks[int(a.get("action_value_2") or 0)] = lab
    ids = {x.get("action_id"): x.get("_i") for x in actions}
    rows, byid, owner = [], {}, {}
    for idx, a in enumerate(actions):
        r = decode_action(a, marks); aid = a.get("action_id"); dep = a.get("_dep") or 0
        r.update(a=a, type=a.get("action_type"), id=aid, i=a.get("_i"), idx=idx, hide=False)
        r["parent"] = owner.get(aid)
        if r["parent"] is None and dep in byid: r["parent"] = byid[dep]["parent"]
        r["dep"] = ids.get(dep) if dep in ids else None
        r["tgt"] = target_text(a) if r["kind"] != "cond" else ""
        if r["kind"] == "cond":
            for k in ("action_detail_2", "action_detail_3"):
                if a.get(k) in ids: owner[a[k]] = idx
        if r["type"] == 7: r["hide"] = True
        rows.append(r); byid[aid] = r
    for r in rows:                                         # type 26 → พับเข้ากับแอ็กชันเป้าหมาย
        if r["type"] == 26 and r["a"].get("action_detail_1") in byid:
            tr = byid[r["a"]["action_detail_1"]]
            if tr["kind"] == "effect" and tr["type"] != 26: tr["formula"] = fold_pass(r["a"], tr, marks); r["hide"] = True
    refd, deps = set(owner), {x["a"].get("_dep") for x in rows}
    for r in rows:        # T45 "初回発動時、以下の効果が発動する" ที่ไม่มีใครอ้างถึง/พึ่งพา → แถวที่ตามมา (จนถึงเงื่อนไขถัดไป) อยู่ภายใต้มัน
        if r["type"] == 45 and r["id"] not in refd and r["id"] not in deps and "以下" in r["desc"]:
            for x in rows[r["idx"] + 1:]:
                if x["kind"] == "cond": break
                x["parent"] = r["idx"]
    children = {}
    for r in rows:
        if r["parent"] is not None and not r["hide"]: children.setdefault(r["parent"], []).append(r)
    items = []
    main = [r for r in rows if r["parent"] is None and r["kind"] != "cond" and not r["hide"]]
    items += [("row", r, False) for r in main]
    def emit(r):
        items.append(("cond" if children.get(r["idx"]) or r["desc"] or r["type"] == 45 else "note", r, False))
        for c in children.get(r["idx"], []):
            if c["kind"] == "cond": emit(c)
            else: items.append(("row", c, True))
    for r in rows:
        if r["parent"] is None and r["kind"] == "cond": emit(r)
    out = ['<table width="100%%" cellspacing="0" cellpadding="6"><tr style="color:%s"><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
        mute, tt("เป้าหมาย", "Target"), tt("เอฟเฟกต์", "Effect"), tt("ค่า / สูตร", "Value / formula"), tt("ระยะเวลา", "Duration"))]
    i = 0
    while i < len(items):
        kind, r, br = items[i]
        if kind in ("cond", "note"):
            tag = ' <span style="color:%s;font-size:11px">[T%s · %s]</span>' % (mute, r["type"], r["a"].get("action_detail_1"))
            jp = ('<br><span style="color:%s;font-size:11px">%s</span>' % (mute, h(r["desc"]))) if r["desc"] else ""
            if kind == "note": out.append('<tr><td colspan="4" align="center" style="color:%s;font-size:11px;border-top:1px solid %s"><i>%s</i>%s</td></tr>' % (mute, line, h(r["name"]), tag))
            else: out.append('<tr><td colspan="4" align="center" style="background:%s;border-top:1px solid %s"><i>%s</i>%s%s</td></tr>' % (panel2, line, h(r["name"]), tag, jp))
            i += 1; continue
        j = i + 1
        while j < len(items) and items[j][0] == "row" and items[j][1]["tgt"] == r["tgt"] and items[j][2] == br: j += 1
        for k in range(i, j):
            x = items[k][1]; dim = "color:%s;" % mute if x["kind"] == "info" else ""
            tcell = ('<td rowspan="%d" align="center" valign="middle" style="border-top:1px solid %s;%s">%s</td>' % (
                j - i, line, ("border-left:3px solid %s;" % acc2) if br else "", h(r["tgt"]))) if k == i else ""
            note = ' <span style="color:%s;font-size:11px">%s</span>' % (mute, tt("↳ ต่อจาก #%d", "↳ after #%d") % x["dep"]) if x["dep"] else ""
            jp = ('<br><span style="color:%s;font-size:11px">%s</span>' % (mute, h(x["desc"]))) if x["desc"] else ""
            dur = (tt("%s วินาที", "%s seconds") % fmtn(x["dur"])) if x["dur"] else "—"
            out.append('<tr>%s<td style="border-top:1px solid %s;%s"><b>%s</b>%s%s <a href="open:skill_action|action_id|%d" style="color:%s">#%s</a></td><td style="border-top:1px solid %s;%s">%s</td><td style="border-top:1px solid %s;%s" align="center">%s</td></tr>' % (
                tcell, line, dim, h(x["name"]), note, jp, x["id"] or 0, acc, x["i"], line, dim, h(x["formula"]).replace("\n", "<br>"), line, dim, h(dur)))
        i = j
    return "".join(out) + "</table>"


# ----------------------------------------------------------------------------- export (XUnity  JP=TH  text files)
_JPCH = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uff66-\uff9f]")
_PH = re.compile(r"\{[^{}]*\}|<[^<>]*>|＜[^＜＞]*＞|%[0-9]*[sd]|[0-9]+(?:\.[0-9]+)?")  # เฉพาะเลขอารบิกครึ่งความกว้าง (３ เต็มความกว้างคงไว้)
_EPI = re.compile(r"^第?[0-9０-９]+[話章節]?$")


def has_jp(s):
    return isinstance(s, str) and bool(_JPCH.search(s))


def nl(s):
    """ขึ้นบรรทัดจริง → \\n แบบตัวอักษร (รูปแบบที่ไฟล์ JP=TH ใช้)"""
    return str(s).replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")


def first_jp(*vals):
    for v in vals:
        if has_jp(v): return nl(v).strip()
    return ""


def action_regex(parts):
    """ต่อคำอธิบายแอ็กชันเป็น regex โครงร่าง: ตัวเลข/ตัวแทนค่า → (\\d+)  แล้วครอบด้วย ^ $"""
    esc = lambda t: re.sub(r"([\\.^$*+?{}\[\]|()])", r"\\\1", t)
    out = ""
    for t in parts:
        t = re.sub(r"\s+|\\n", "", str(t)); pos = 0
        for m in _PH.finditer(t):
            out += esc(t[pos:m.start()]) + r"(\d+)"; pos = m.end()
        out += esc(t[pos:])
    return "^" + out + "$"


def skill_section(key):
    if key in ("union_burst", "union_burst_evolution"): return "UB"
    if key == "sp_union_burst": return "SPUB"
    m = re.match(r"(main|ex|sp)_skill_(?:evolution_|revolution_)?(\d+)$", key)
    if not m: return key.upper()
    n = int(m.group(2))
    return {"main": "S%d" % n, "ex": "EX" if n == 1 else "EX%d" % n, "sp": "SP%d" % n}[m.group(1)]


_DATE = re.compile(r"^[0-9０-９]{1,2}月[0-9０-９]{1,2}日$")


def profile_info_values(d):
    """ค่าโปรไฟล์ที่แสดงจริง: ใช้ unit_profile_display_override ถ้ามี ไม่งั้นใช้ unit_profile (ไม่เอา guild)"""
    ov = [r.get("unknown_4") for r in d.get("override", []) if r.get("unknown_2") == 1 and r.get("unknown_3")]
    if ov: vals = ov
    else:
        p = d["profile"]; vals = [p.get(k) for k in ("voice", "race", "favorite", "blood_type", "age")]
    return [v for v in vals if has_jp(v) and not _DATE.match(v.strip())]


def build_profile_skills(d, o):
    """ไฟล์แบบ AlmondEye.txt : ##Profile## (ตัวเลือก) ##UE## (ตัวเลือก) ##UB## ##S1## ##S2## ##EX## ..."""
    seen, n = set(), 0
    def add(lst, jp, en=""):
        nonlocal n
        jp = (jp or "").strip()
        if jp and jp not in seen: seen.add(jp); lst.append(jp + "=" + en); n += 1
    def en_of(v):      # อังกฤษเฉพาะข้อความที่ไม่มีตัวญี่ปุ่นปน และเปิดตัวเลือกไว้
        return nl(v).strip() if o.get("en", True) and isinstance(v, str) and v.strip() and not has_jp(v) else ""
    parts = []
    if o.get("profile"):
        u, p = d["unit"], d["profile"]; a, b, c = [], [], []
        if o.get("p_comment", True) and has_jp(u.get("comment")): add(a, nl(u["comment"]))
        if o.get("p_info", True):
            for v in profile_info_values(d): add(b, nl(v))
        if o.get("p_self", True) and has_jp(p.get("self_text")): add(b, nl(p["self_text"]))
        if o.get("p_catch", True) and has_jp(p.get("catch_copy")): add(b, nl(p["catch_copy"]))
        if o.get("p_story", True):
            for r in d["story"]:
                v = (r.get("sub_title") or "").strip()
                if has_jp(v): add(c, nl(v))
        blocks = ["\n".join(x) for x in (a, b, c) if x]
        if blocks: parts.append("##Profile##\n" + "\n\n".join(blocks))
    if o.get("ue"):
        lines = []
        for e in d.get("ue", []):
            add(lines, first_jp(e.get("equipment_name"))); add(lines, first_jp(e.get("description")))
        if lines: parts.append("##UE##\n" + "\n".join(lines))
    keys = o.get("keys")
    order = {k: i for i, k in enumerate(SKILL_ORDER)}
    secs = {}
    for s in sorted(d["skills"], key=lambda x: order.get(x["key"], 999)):
        if keys is not None and s["key"] not in keys: continue
        sec = skill_section(s["key"]); sd = s["data"]; lines = []
        add(lines, first_jp(sd.get("name_jp"), sd.get("name")), en_of(sd.get("name")))
        want = o.get("ex_desc") if sec.startswith("EX") else o.get("desc", True)
        if want:
            add(lines, first_jp(sd.get("description_jp"), sd.get("description")), en_of(sd.get("description")))
            acts = [x.get("description") for x in s["actions"] if x.get("description")]
            if o.get("regex", True) and acts:
                rx = action_regex(acts)
                if rx not in seen: seen.add(rx); lines.append('r:"%s"=' % rx); n += 1
        if lines: secs.setdefault(sec, []).extend(lines)
    for sec, lines in secs.items(): parts.append("##%s##\n" % sec + "\n".join(lines))
    return "\n\n".join(parts) + "\n", n


def build_hs_comments(d, o):
    """ไฟล์แบบ AlmondEye_HS_TH.txt : บรรทัดละ 1 ข้อความ  JP=  แต่ละกลุ่มคั่นด้วยบรรทัดว่าง 2 บรรทัด"""
    seen, n, groups = set(), 0, []
    for key, rows in (("room", d["room"]), ("comments", d["comments"]), ("album", d.get("album", []))):
        if not o.get(key, key != "album"): continue
        g = []
        for r in rows:
            t = nl(r.get("description") or "")
            if t.strip() and t not in seen: seen.add(t); g.append(t + "="); n += 1
        if g: groups.append("\n".join(g))
    return "\n\n\n".join(groups) + "\n", n


class OptionsDialog(QDialog):
    def __init__(self, parent, title, items):
        super().__init__(parent); self.setWindowTitle(title); self.setMinimumWidth(460)
        lay = QVBoxLayout(self); lay.setContentsMargins(20, 18, 20, 16); lay.setSpacing(10)
        ink = parent.win.theme["ink"]; self.boxes = {}
        for key, label, on in items:
            cb = QCheckBox(label); cb.setChecked(on); cb.setStyleSheet("QCheckBox{color:%s}" % ink); lay.addWidget(cb); self.boxes[key] = cb
        row = QHBoxLayout(); row.addStretch()
        ok = QPushButton(tt("เลือกที่เก็บไฟล์…", "Choose save location…")); ok.setObjectName("pri"); cancel = QPushButton(tt("ยกเลิก", "Cancel"))
        ok.clicked.connect(self.accept); cancel.clicked.connect(self.reject); row.addWidget(cancel); row.addWidget(ok); lay.addLayout(row)

    def values(self):
        return {k: b.isChecked() for k, b in self.boxes.items()}


class ExportSkillsDialog(QDialog):
    def __init__(self, parent, d):
        super().__init__(parent); self.setWindowTitle(tt("ส่งออก โปรไฟล์ + สกิล", "Export profile + skills")); self.setMinimumWidth(600)
        ink = parent.win.theme["ink"]; self.boxes = {}
        lay = QVBoxLayout(self); lay.setContentsMargins(20, 18, 20, 16); lay.setSpacing(7)
        def cb(key, text, on, indent=0):
            c = QCheckBox(text); c.setChecked(on); c.setStyleSheet("QCheckBox{color:%s;margin-left:%dpx}" % (ink, indent * 24)); lay.addWidget(c); self.boxes[key] = c; return c
        lay.addWidget(lbl(tt("โปรไฟล์ (ตัวเลือก — ปิดไว้เป็นค่าเริ่มต้น)", "Profile (optional — off by default)"), mute=True))
        cb("profile", tt("รวมส่วน ##Profile##", "Include the ##Profile## section"), False)
        subs = [cb("p_comment", tt("คำอธิบายตัวละคร (unit_data.comment)", "Character description (unit_data.comment)"), True, 1),
                cb("p_info", tt("CV / เผ่าพันธุ์ / งานอดิเรก / น้ำหนัก … (unit_profile_display_override ถ้าไม่มีใช้ unit_profile)", "CV / race / hobby / weight … (unit_profile_display_override, else unit_profile)"), True, 1),
                cb("p_self", tt("ข้อความแนะนำตัว (self_text)", "Self-introduction (self_text)"), True, 1),
                cb("p_catch", tt("แคตช์คอปปี้ (catch_copy)", "Catch copy (catch_copy)"), True, 1),
                cb("p_story", tt("ชื่อตอนเนื้อเรื่อง (sub_title — ไม่รวมบรรทัด “… 第N話”)", "Story episode titles (sub_title — without the “… 第N話” lines)"), True, 1)]
        for c in subs: c.setEnabled(False)
        self.boxes["profile"].toggled.connect(lambda on: [c.setEnabled(on) for c in subs])
        uecb = cb("ue", tt("อาวุธเฉพาะ (ชื่อ + คำอธิบาย → ##UE##)", "Unique equipment (name + description → ##UE##)"), False)
        if not d.get("ue"):
            uecb.setEnabled(False); uecb.setText(uecb.text() + tt("   — (หน่วยนี้ไม่มีอาวุธเฉพาะใน DB)", "   — (this unit has no unique equipment in the DB)"))
        lay.addSpacing(4); lay.addWidget(lbl(tt("เลือกสกิลที่ต้องการส่งออก (เช่น เฉพาะ S1++)", "Choose which skills to export (e.g. only S1++)"), mute=True))
        self.lst = QListWidget(); self.lst.setMinimumHeight(230); lay.addWidget(self.lst)
        order = {k: i for i, k in enumerate(SKILL_ORDER)}
        for s in sorted(d["skills"], key=lambda x: order.get(x["key"], 999)):
            sd = s["data"]; it = QListWidgetItem("%s   ·   %s   /   %s" % (skill_tag(s["key"]), sd.get("name") or "", sd.get("name_jp") or ""))
            it.setData(Qt.UserRole, s["key"]); it.setFlags(it.flags() | Qt.ItemIsUserCheckable); it.setCheckState(Qt.Checked); self.lst.addItem(it)
        qr = QHBoxLayout()
        for text, fn in ((tt("เลือกทั้งหมด", "Select all"), lambda k: True), (tt("ไม่เลือกเลย", "Select none"), lambda k: False),
                         (tt("เฉพาะเวอร์ชัน + / ++", "Only + / ++ versions"), lambda k: bool(re.search("evolution|revolution", k)))):
            b = QPushButton(text); b.clicked.connect(lambda _=0, fn=fn: self.set_all(fn)); qr.addWidget(b)
        qr.addStretch(); lay.addLayout(qr)
        lay.addSpacing(4); lay.addWidget(lbl(tt("เนื้อหาของแต่ละสกิล", "Content of each skill"), mute=True))
        cb("desc", tt("คำอธิบายสกิล (description_jp)", "Skill description (description_jp)"), True)
        cb("regex", tt('บรรทัด regex ของแอ็กชัน   r:"^…$"=', 'Action regex line   r:"^…$"='), True)
        cb("ex_desc", tt("รวมคำอธิบาย (และ regex) ของ EX สกิล — ปิดไว้ตามไฟล์ตัวอย่าง", "Include EX skill descriptions (and regex) — off, like the sample file"), False)
        cb("en", tt("ใส่ข้อความอังกฤษหลัง = เมื่อ DB มี (ชื่อ/คำอธิบายสกิล) → รูปแบบ JP=EN", "Fill the English text after = when the DB has it (skill names / descriptions) → JP=EN"), True)
        row = QHBoxLayout(); row.addStretch()
        ok = QPushButton(tt("เลือกที่เก็บไฟล์…", "Choose save location…")); ok.setObjectName("pri"); cancel = QPushButton(tt("ยกเลิก", "Cancel"))
        ok.clicked.connect(self.accept); cancel.clicked.connect(self.reject); row.addWidget(cancel); row.addWidget(ok); lay.addLayout(row)

    def set_all(self, fn):
        for i in range(self.lst.count()):
            it = self.lst.item(i); it.setCheckState(Qt.Checked if fn(it.data(Qt.UserRole)) else Qt.Unchecked)

    def values(self):
        v = {k: b.isChecked() for k, b in self.boxes.items()}
        v["keys"] = {self.lst.item(i).data(Qt.UserRole) for i in range(self.lst.count()) if self.lst.item(i).checkState() == Qt.Checked}
        return v


class CharTab(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win; self.uid = None; self.ids = []
        lay = QVBoxLayout(self); lay.setContentsMargins(14, 8, 14, 10); lay.setSpacing(8)
        r = QHBoxLayout()
        self.ed = QLineEdit(); self.ed.setPlaceholderText(tt("🗺 พิมพ์ชื่อตัวละคร (EN/JP) หรือ Unit ID แล้วกด Enter…  เช่น Hiyori, ヒヨリ, 100101", "🗺 Type a character name (EN/JP) or Unit ID, then press Enter…  e.g. Hiyori, ヒヨリ, 100101")); self.ed.setMinimumHeight(36)
        self.prev = QPushButton("‹"); self.next = QPushButton("›"); go = QPushButton(tt("แสดง", "Show")); go.setObjectName("pri")
        r.addWidget(self.prev); r.addWidget(self.ed, 1); r.addWidget(self.next); r.addWidget(go); lay.addLayout(r)
        nav = QHBoxLayout()
        for text, a in ((tt("ข้อมูลพื้นฐาน", "Basic info"), "base"), (tt("โปรไฟล์", "Profile"), "profile"), (tt("สกิล", "Skills"), "skills"), (tt("เนื้อเรื่อง", "Story"), "story"), (tt("คอมเมนต์/เสียง", "Comments/Voice"), "voice"), ("Room", "room"), (tt("อาวุธเฉพาะ", "Unique equip"), "ue"), (tt("ตารางที่เกี่ยวข้อง", "Related tables"), "related")):
            b = QPushButton(text); b.setObjectName("pill"); b.clicked.connect(lambda _=0, a=a: self.view.scrollToAnchor(a)); nav.addWidget(b)
        nav.addStretch(); lay.addLayout(nav)
        er = QHBoxLayout(); er.addWidget(lbl(tt("ส่งออกรูปแบบ XUnity (JP=EN) ของตัวละครนี้:", "Export this character in XUnity format (JP=EN):"), mute=True))
        self.ex1 = QPushButton(tt("⬇ โปรไฟล์ + สกิล", "⬇ Profile + skills")); self.ex2 = QPushButton(tt("⬇ คอมเมนต์/เสียง (HS)", "⬇ Comments / voice (HS)"))
        self.ex1.setToolTip(tt("ไฟล์แบบ AlmondEye.txt — ##Profile## ##UB## ##S1## ##S2## ##EX##", "AlmondEye.txt style — ##Profile## ##UB## ##S1## ##S2## ##EX##"))
        self.ex2.setToolTip(tt("ไฟล์แบบ AlmondEye_HS_TH.txt — ข้อความเสียง/คอมเมนต์ บรรทัดละข้อความ", "AlmondEye_HS_TH.txt style — voice / comment lines, one per line"))
        self.exi = QPushButton(tt("🖼 โฟลเดอร์ไอคอนสกิล…", "🖼 Skill icon folder…"))
        er.addWidget(self.ex1); er.addWidget(self.ex2); er.addStretch(); er.addWidget(self.exi); lay.addLayout(er)
        self.ex1.clicked.connect(lambda: self.export_file("skills")); self.ex2.clicked.connect(lambda: self.export_file("hs")); self.exi.clicked.connect(self.pick_icon_dir)
        from PySide6.QtWidgets import QTextBrowser
        self.view = QTextBrowser(); self.view.setOpenLinks(False); self.view.anchorClicked.connect(self.link)
        self.view.setStyleSheet("QTextBrowser{background:%s;border:1px solid %s;border-radius:12px;padding:8px}" % (win.theme["panel"], win.theme["line"]))
        lay.addWidget(self.view, 1)
        go.clicked.connect(self.search); self.ed.returnPressed.connect(self.search)
        self.prev.clicked.connect(lambda: self.step(-1)); self.next.clicked.connect(lambda: self.step(1))
        self.placeholder()

    def placeholder(self):
        t = self.win.theme
        self.view.setHtml('<div style="color:%s;padding:40px;text-align:center"><h2>' % t["mute"] + tt("🗺 แผนที่ตัวละคร</h2>พิมพ์ชื่อหรือ Unit ID ด้านบน เพื่อรวมข้อมูลทุกตารางของตัวละครนั้นไว้หน้าเดียว<br>"
                          "โปรไฟล์ · คอมเมนต์ · เสียง · เนื้อเรื่อง · สกิลและแอ็กชัน · Room", "🗺 Character map</h2>Type a name or Unit ID above to gather every table's data for that character in one page<br>"
                          "Profile · Comments · Voice · Story · Skills & actions · Room") + "</div>")

    def refresh_names(self):
        from PySide6.QtWidgets import QCompleter
        self.ids = sorted(self.win.db.names)
        items = ["%d  %s" % (i, self.win.db.names[i]) for i in self.ids]
        comp = QCompleter(items, self); comp.setCaseSensitivity(Qt.CaseInsensitive); comp.setFilterMode(Qt.MatchContains); self.ed.setCompleter(comp)
        comp.activated.connect(lambda t: self.show_uid(int(t.split()[0])))
        comp.setMaxVisibleItems(12); self.style_popup(comp)

    def style_popup(self, comp):
        t = self.win.theme
        comp.popup().setStyleSheet(
            "QListView{background:%s;color:%s;border:1px solid %s;outline:0;padding:4px}"
            "QListView::item{padding:7px 12px;border-radius:6px}"
            "QListView::item:hover{background:%s}"
            "QListView::item:selected{background:%s;color:%s}" % (t["panel"], t["ink"], t["acc"], t["panel2"], t["accbg"], t["ink"]))

    def search(self):
        t = self.ed.text().strip()
        if not t: return
        m = re.match(r"^(\d{4,7})", t)
        if m: return self.show_uid(int(m.group(1)))
        tl = t.lower(); names = self.win.db.names
        hits = [i for i in self.ids if tl in names[i].lower()]
        if not hits:  # ลองชื่อญี่ปุ่น
            try:
                c = self.win.db.connect()
                hits = [r[0] for r in c.execute("select unit_id from unit_data where unit_name_jp like ? or kana like ? order by unit_id", ("%" + t + "%", "%" + t + "%"))]
                c.close()
            except Exception: pass
        if not hits: self.view.setHtml(tt("<h3>ไม่พบตัวละคร “%s”</h3>", "<h3>Character “%s” not found</h3>") % h(t)); return
        self.show_uid(hits[0])
        if len(hits) > 1: self.win.status(tt("พบ %d รายการ — แสดงรายการแรก (ใช้ปุ่ม ‹ › เพื่อเลื่อน)", "%d matches — showing the first (use ‹ › to step)") % len(hits))

    def export_file(self, kind):
        db = self.win.db
        if not self.uid or not db.path:
            QMessageBox.information(self, APP, tt("เลือกตัวละครในแท็บนี้ก่อน (พิมพ์ชื่อหรือ Unit ID แล้วกด Enter)", "Pick a character in this tab first (type a name or Unit ID, then Enter)")); return
        uid = self.uid
        try: d = db.char_map(uid)
        except Exception as e: QMessageBox.warning(self, APP, str(e)); return
        if kind == "skills":
            dlg = ExportSkillsDialog(self, d)
        else:
            items = [("room", tt("คอมเมนต์ห้อง (room_unit_comments)", "Room comments (room_unit_comments)"), True),
                     ("comments", tt("คอมเมนต์/เสียงตัวละคร (unit_comments) — รวมทุกเวอร์ชันดาว", "Character comments / voice (unit_comments) — all star versions"), True),
                     ("album", tt("คำพูดในอัลบั้มเสียง (album_voice_list)", "Voice album lines (album_voice_list)"), False)]
            dlg = OptionsDialog(self, tt("ส่งออก คอมเมนต์/เสียง (HS)", "Export comments / voice (HS)"), items)
        title = dlg.windowTitle()
        if not dlg.exec(): return
        opts = dlg.values()
        nm = re.sub(r"[^0-9A-Za-z]+", "", db.names.get(uid, "")) or str(uid)
        start = os.path.join(str(self.win.s.value("exportdir", "") or ""), nm + (".txt" if kind == "skills" else "_HS_TH.txt"))
        p, _ = QFileDialog.getSaveFileName(self, title, start, "Text (*.txt)")
        if not p: return
        self.win.s.setValue("exportdir", os.path.dirname(p))
        def work():
            text, n = (build_profile_skills if kind == "skills" else build_hs_comments)(d, opts)
            if n:
                with open(p, "w", encoding="utf-8", newline="\n") as f: f.write(text)
            return n
        t = Task(work, self); self.win.keep(t)
        def done(res, err):
            if err: QMessageBox.warning(self, APP, err); return
            if not res: QMessageBox.information(self, APP, tt("ไม่มีข้อมูลให้ส่งออกตามหัวข้อที่เลือก", "Nothing to export for the selected sections")); return
            self.win.status(tt("ส่งออกแล้ว: %s (%d บรรทัด)", "Exported: %s (%d lines)") % (p, res))
        t.done.connect(done); t.start()

    def pick_icon_dir(self):
        p = QFileDialog.getExistingDirectory(self, tt("เลือกโฟลเดอร์ไอคอนสกิล (icon_skill_*.png)", "Choose the skill icon folder (icon_skill_*.png)"), self.win.icon_dir() or "")
        if not p: return
        self.win.s.setValue("icondir", p); self.win._icondir = None
        if self.uid: self.show_uid(self.uid)

    def step(self, d):
        if not self.ids: return
        if self.uid in self.ids: i = (self.ids.index(self.uid) + d) % len(self.ids)
        else: i = 0
        self.show_uid(self.ids[i])

    def show_uid(self, uid):
        self.uid = uid; self.ed.setText("%d  %s" % (uid, self.win.db.names.get(uid, "")))
        self.view.setHtml(tt("<h3>⏳ กำลังรวบรวมข้อมูล…</h3>", "<h3>⏳ Gathering data…</h3>"))
        t = Task(lambda: self.win.db.char_map(uid), self); self.win.keep(t)
        def done(res, err):
            if err: self.view.setHtml("<h3>⚠ %s</h3>" % h(err)); return
            if self.uid == uid: self.view.setHtml(self.render(res))
        t.done.connect(done); t.start()

    def link(self, url):
        from urllib.parse import unquote
        s = unquote(url.toString())
        if s.startswith("open:"):
            tbl, col, val = s[5:].split("|", 2); self.win.open_table(tbl, filters={col: "=" + val} if col else None)
        elif s.startswith("char:"): self.show_uid(int(s[5:]))
        elif s.startswith("#"): self.view.scrollToAnchor(s[1:])

    # ------ HTML
    def render(self, d):
        T = self.win.theme; names = self.win.db.names
        u, p = d["unit"], d["profile"]
        mute, acc, acc2, line, bg2, ink = T["mute"], T["acc"], T["acc2"], T["line"], T["bg2"], T["ink"]
        def sec(anchor, title, body, count=None):
            return ('<a name="%s"></a><table width="100%%" cellspacing="0" cellpadding="8" style="margin-top:18px"><tr><td style="background:%s;border-left:4px solid %s">'
                    '<span style="font-size:16px;font-weight:700">%s</span> <span style="color:%s">%s</span></td></tr></table>%s' % (anchor, T["panel2"], acc, title, mute, ("(%d)" % count) if count is not None else "", body))
        def kv(rows):
            out = '<table width="100%" cellspacing="0" cellpadding="6">'
            for k, v in rows:
                if v in (None, "", 0, "0") and k not in ("rarity",): continue
                out += '<tr><td width="170" style="color:%s;border-bottom:1px solid %s">%s</td><td style="border-bottom:1px solid %s">%s</td></tr>' % (mute, line, h(k), line, v if isinstance(v, str) and v.startswith("<") else h(v))
            return out + "</table>"
        nm = h(u.get("unit_name") or p.get("unit_name") or names.get(d["uid"], "")); jp = h(u.get("unit_name_jp") or p.get("unit_name_jp") or "")
        out = ['<div style="font-size:12px;color:%s">Unit ID %d · Chara ID %d</div>' % (mute, d["uid"], d["chara"]),
               '<div style="font-size:26px;font-weight:800;color:%s">%s <span style="font-size:16px;color:%s">%s %s</span></div>' % (acc2, nm, mute, jp, ("· " + h(u.get("kana"))) if u.get("kana") else "")]
        if p.get("catch_copy"): out.append('<div style="font-size:14px;color:%s">「%s」</div>' % (acc, h(p["catch_copy"])))
        if u.get("comment"): out.append('<p style="margin-top:8px">%s</p>' % h(u["comment"]))
        # --- base
        atk = {1: "1 (กายภาพ)", 2: "2 (เวท)"}.get(u.get("atk_type"), u.get("atk_type"))
        out.append(sec("base", "📌 ข้อมูลพื้นฐาน (unit_data)", kv([
            ("ความหายากเริ่มต้น (rarity)", u.get("rarity")), ("ประเภทโจมตี (atk_type)", atk), ("ตำแหน่ง (search_area_width)", u.get("search_area_width")),
            ("ความเร็วเดิน (move_speed)", u.get("move_speed")), ("เวลาโจมตีปกติ", u.get("normal_atk_cast_time")), ("กิลด์ (guild_id)", u.get("guild_id")),
            ("เปิดตัว", u.get("start_time")), ("สิ้นสุด", u.get("end_time")), ("ตัวละครจำกัด (is_limited)", u.get("is_limited")), ("เป็นคอลแลบ (is_collab)", u.get("is_collab")),
            ("ตัวต้นฉบับ (original_unit_id)", ('<a href="char:%d" style="color:%s">%d %s</a>' % (u["original_unit_id"], acc, u["original_unit_id"], h(names.get(u["original_unit_id"], ""))) if u.get("original_unit_id") else None)),
        ]) + self.atk_html(d)))
        # --- profile
        bd = ("%s/%s" % (p.get("birth_month"), p.get("birth_day"))) if p.get("birth_month") else ""
        ov = [(r.get("unknown_3"), r.get("unknown_4")) for r in d.get("override", []) if r.get("unknown_2") == 1 and r.get("unknown_3")]
        out.append(sec("profile", "🪪 โปรไฟล์ (unit_profile)", kv([
            ("CV (นักพากย์)", p.get("voice")), ("หมู่เลือด", p.get("blood_type")), ("วันเกิด (เดือน/วัน)", bd), ("อายุ", p.get("age")), ("ส่วนสูง", p.get("height")),
            ("น้ำหนัก", p.get("weight")), ("เผ่าพันธุ์ (race)", p.get("race")), ("งานอดิเรก/ชอบ (favorite)", p.get("favorite")), ("กิลด์", p.get("guild")),
            ("แนะนำตัว (self_text)", p.get("self_text"))] + [("↳ " + lab, val) for lab, val in ov])))
        # --- skills
        out.append(sec("skills", "✨ สกิลและความสามารถ (unit_skill_data → skill_data → skill_action)", self.skills_html(d), len(d["skills"])))
        # --- unique equipment (unit_unique_equipment → unique_equipment_data)
        ue = ""
        for e in d.get("ue", []):
            stt = ", ".join("%s +%s" % (UE_STAT[k], fmtn(e[k])) for k in UE_STAT if e.get(k))
            extra = self.ue_extra(d, e)
            ue += ('<table width="100%%" cellspacing="0" cellpadding="8" style="margin-top:10px;border:1px solid %s"><tr><td style="background:%s">'
                   '<span style="color:%s;font-weight:700">%s %s</span> &nbsp; <a href="open:unique_equipment_data|equipment_id|%d" style="color:%s">Equip ID %d</a>'
                   ' <span style="color:%s">· require_level %s · promotion_level %s</span><br><span style="font-size:15px;font-weight:700">%s</span><br>%s<br>'
                   '<span style="color:%s">%s %s</span></td></tr></table>' % (
                       line, T["panel2"], acc2, tt("ช่อง", "Slot"), e.get("equip_slot"), e["equipment_id"], acc, e["equipment_id"], mute, e.get("require_level"), e.get("promotion_level"),
                       h(e.get("equipment_name")), h(e.get("description")), mute, tt("ค่าสถานะพื้นฐาน:", "Base stats:"), h(stt))) + extra
        out.append(sec("ue", tt("🗡 อาวุธเฉพาะ (unit_unique_equipment → unique_equipment_data)", "🗡 Unique equipment (unit_unique_equipment → unique_equipment_data)"),
                       ue if ue else '<p style="color:%s">%s</p>' % (mute, tt("ไม่มีข้อมูล", "No data")), len(d.get("ue", []))))
        # --- story
        out.append(sec("story", "📖 เนื้อเรื่อง (story_detail / chara_story_status)", self.story_html(d), len(d["story"])))
        # --- voice / comments
        cm = '<table width="100%" cellspacing="0" cellpadding="6">'
        for r in d["comments"]:
            tgt = (' <span style="color:%s">→ %s</span>' % (acc, h(names.get(r["target_unit_id"], r["target_unit_id"])))) if r.get("target_unit_id") else ""
            cm += '<tr><td width="130" style="color:%s;border-bottom:1px solid %s">%s · type %s · #%s</td><td style="border-bottom:1px solid %s">%s%s</td></tr>' % (mute, line, r.get("unit_id"), r.get("use_type"), r.get("voice_id"), line, h(r.get("description")), tgt)
        cm += "</table>"
        out.append(sec("voice", "💬 คอมเมนต์/เสียงตัวละคร (unit_comments)", cm if d["comments"] else '<p style="color:%s">ไม่มีข้อมูล</p>' % mute, len(d["comments"])))
        rm = '<table width="100%" cellspacing="0" cellpadding="6">'
        for r in d["room"]:
            rm += '<tr><td width="190" style="color:%s;border-bottom:1px solid %s">%s · trigger %s · ความสนิท %s · #%s</td><td style="border-bottom:1px solid %s">%s</td></tr>' % (mute, line, r.get("unit_id"), r.get("trigger"), r.get("beloved_step"), r.get("voice_id"), line, h(r.get("description")))
        rm += "</table>"
        out.append(sec("room", "🏠 Room Comment (room_unit_comments)", rm if d["room"] else '<p style="color:%s">ไม่มีข้อมูล</p>' % mute, len(d["room"])))
        rel = "".join('<a href="open:|%s|%s" style="color:%s;text-decoration:none">&nbsp;◆ %s</a> <span style="color:%s">%d</span>&nbsp;&nbsp;&nbsp;' % ("", "", acc, "", mute, 0) for _ in [])
        rel = " &nbsp; ".join('<a href="open:%s|unit_id|%d" style="color:%s">%s</a> <span style="color:%s">(%d)</span>' % (t, d["uid"], acc, t, mute, n) for t, n in d["related"])
        out.append(sec("related", "🔗 ตารางอื่นที่มีข้อมูลของ Unit ID นี้ (คลิกเพื่อเปิดพร้อมกรอง)", '<p style="line-height:190%%">%s</p>' % rel, len(d["related"])))
        return tx('<div style="color:%s">%s</div>' % (ink, "".join(out)))

    SP_COL = {"attack": "atk", "defense": "def", "magic_attack": "magic_str", "magic_defense": "magic_def", "critical": "physical_critical",
              "magic_critical": "magic_critical", "penetration": "physical_penetrate", "magic_penetration": "magic_penetrate", "accuracy": "accuracy",
              "dodge": "dodge", "life_steal": "life_steal", "wave_hp_recovery": "wave_hp_recovery", "wave_energy_recovery": "wave_energy_recovery",
              "hp_recovery_rate": "hp_recovery_rate", "energy_recovery_rate": "energy_recovery_rate", "energy_reduce_rate": "energy_reduce_rate", "hp": "hp"}

    def ue_extra(self, d, e):
        """ค่าสถานะตามเลเวลของ UE ช่อง 1 + ข้อมูล SP (ex_unique_equipment_1 → สกิล ++)"""
        import math
        T = self.win.theme; mute, line, acc = T["mute"], T["line"], T["acc"]
        eid = e["equipment_id"]; rates = [r for r in d.get("ue_rate", []) if r["equipment_id"] == eid]
        def at(base, lv):          # base + Σ(อัตรา × จำนวนเลเวลในแต่ละช่วง min_lv..max_lv)  ปัดขึ้น
            out = {}
            for k in UE_STAT:
                v = base.get(k) or 0
                for rt in rates:
                    lo, hi = rt.get("min_lv") or 1, rt.get("max_lv") or -1
                    v += (rt.get(k) or 0) * max(0, (lv if hi <= 0 else min(lv, hi)) - lo + 1)
                if v: out[k] = math.ceil(v - 1e-9)
            return out
        fs = lambda st: ", ".join("%s +%s" % (UE_STAT[k], fmtn(v)) for k, v in st.items()) or "—"
        rows_ = ""
        if e.get("equip_slot") == 1 and rates:
            rows_ += '<tr><td style="color:%s">%s</td><td>%s</td></tr>' % (mute, tt("ค่าสถานะที่ Lv 370", "Stats at Lv 370"), h(fs(at(e, 370))))
        sp = next((r for r in d.get("ue_sp", []) if r["equipment_id"] == eid), None)
        if sp:
            base = {self.SP_COL[k]: sp.get(k) for k in self.SP_COL if sp.get(k)}
            iid = sp.get("required_item_id")
            rows_ += '<tr><td style="color:%s">%s</td><td>%s</td></tr>' % (mute, tt("SP: ต้องใช้", "SP: requires"), '%s × <a href="open:item_data|item_id|%d" style="color:%s">%s</a>' % (
                fmtn(sp.get("required_item_count")), iid, acc, h(d["ue_items"].get(iid, "item %s" % iid))))
            sk = [s for s in d["skills"] if "revolution" in s["key"]]
            rows_ += '<tr><td style="color:%s">%s</td><td>%s</td></tr>' % (mute, tt("SP: ปลดล็อกสกิล", "SP: unlocks skill"), "<br>".join(
                '<b>%s</b> %s <a href="open:skill_data|skill_id|%d" style="color:%s">Skill ID %d</a>' % (h(skill_tag(s["key"])), h(s["data"].get("name_jp")), s["skill_id"], acc, s["skill_id"]) for s in sk) or "—")
            rows_ += '<tr><td style="color:%s">%s</td><td>%s <span style="color:%s;font-size:11px">%s</span></td></tr>' % (mute, tt("SP: ค่าสถานะที่ Lv 390 (?)", "SP: stats at Lv 390 (?)"), h(fs(at(base, 390))), mute,
                tt("เพดานเลเวล SP ไม่พบใน DB — 390 เป็นค่าที่ตรงกับตัวเลขบนวิกิ", "SP level cap is not in the DB — 390 is the value that matches the wiki figures"))
        if not rows_: return ""
        return '<table width="100%%" cellspacing="0" cellpadding="6" style="border:1px solid %s;border-top:0">%s</table>' % (line, rows_)

    def atk_html(self, d):
        if not d["atk"]: return ""
        def nm(x):
            return "AA" if x == 1 else ("S%d" % (x - 1000) if 1000 < x < 2000 else ("SP%d" % (x - 2000) if x > 2000 else str(x)))
        out = ""
        for a in d["atk"]:
            seq = [int(a["atk_pattern_%d" % i]) for i in range(1, 21) if a.get("atk_pattern_%d" % i)]
            ls, le = int(a.get("loop_start") or 1), int(a.get("loop_end") or len(seq))
            ini, loop = seq[:max(ls - 1, 0)], seq[max(ls - 1, 0):le]
            out += ('<p style="color:%s">%s <span style="font-size:11px">(unit_attack_pattern #%s)</span><br><b style="color:%s">%s :</b> %s<br><b style="color:%s">%s :</b> %s</p>' % (
                self.win.theme["mute"], tt("ลำดับการโจมตี", "Attack sequence"), a.get("pattern_id"),
                self.win.theme["ink"], tt("เริ่มต้น", "Initial"), " → ".join(map(nm, ini)) or "—",
                self.win.theme["ink"], tt("วนซ้ำ", "Loop"), " → ".join(map(nm, loop)) or "—"))
        return out

    def skills_html(self, d):
        T = self.win.theme; mute, acc, acc2, line = T["mute"], T["acc"], T["acc2"], T["line"]
        if not d["skills"]: return '<p style="color:%s">ไม่มีข้อมูลสกิล</p>' % mute
        order = {k: i for i, k in enumerate(SKILL_ORDER)}
        out = ""
        for s in sorted(d["skills"], key=lambda x: order.get(x["key"], 999)):
            sd = s["data"]; ic = self.win.icon_url(sd.get("icon_type"))
            img = ('<img src="%s" width="48" height="48">' % ic) if ic else ""
            out += ('<table width="100%%" cellspacing="0" cellpadding="8" style="margin-top:12px;border:1px solid %s"><tr><td style="background:%s">'
                    '<table cellspacing="0" cellpadding="0"><tr><td width="62" valign="top">%s</td><td>'
                    '<span style="color:%s;font-weight:700">%s</span> &nbsp; <a href="open:skill_data|skill_id|%d" style="color:%s">Skill ID %d</a><br>'
                    '<span style="font-size:15px;font-weight:700">%s</span> <span style="color:%s">%s</span><br>%s<br><span style="color:%s">%s</span>'
                    '<br><span style="color:%s;font-size:11px">cast %s s · type %s · icon %s · area %s</span></td></tr></table></td></tr>' % (
                        line, T["panel2"], img, acc2, h(skill_label(s["key"])), s["skill_id"], acc, s["skill_id"], h(sd.get("name")), mute, h(sd.get("name_jp")),
                        h(sd.get("description")), mute, h(sd.get("description_jp")), mute, sd.get("skill_cast_time"), sd.get("skill_type"), sd.get("icon_type"), sd.get("skill_area_width")))
            if s["actions"]: out += "<tr><td>" + action_table_html(s["actions"], T) + "</td></tr>"
            out += "</table>"
        return out

    def story_html(self, d):
        T = self.win.theme; mute, acc, line = T["mute"], T["acc"], T["line"]
        if not d["story"]: return '<p style="color:%s">ไม่มีข้อมูลเนื้อเรื่องของตัวละครนี้ (เนื้อหาบทสนทนาเก็บในไฟล์ asset ของเกม ไม่ได้อยู่ในฐานข้อมูลนี้)</p>' % mute
        bonus = {b["story_id"]: b for b in d["bonus"]}
        out = '<table width="100%" cellspacing="0" cellpadding="6"><tr style="color:' + mute + '"><td>ตอน</td><td>ชื่อตอน</td><td>ความสนิท</td><td>โบนัสสถานะ</td></tr>'
        for r in d["story"]:
            b = bonus.get(r["story_id"]); bt = ""
            if b:
                bt = ", ".join("%s +%s" % (STORY_STAT.get(b["status_type_%d" % i], "type %s" % b["status_type_%d" % i]), b["status_rate_%d" % i]) for i in range(1, 6) if b.get("status_type_%d" % i))
            out += '<tr><td style="border-top:1px solid %s"><a href="open:story_detail|story_id|%d" style="color:%s">%s</a></td><td style="border-top:1px solid %s"><b>%s</b></td><td style="border-top:1px solid %s">%s</td><td style="border-top:1px solid %s">%s</td></tr>' % (
                line, r["story_id"], acc, h(r.get("title")), line, h(r.get("sub_title")), line, r.get("love_level") or "", line, h(bt))
        out += "</table>"
        ids = set()
        for b in d["bonus"]:
            for i in range(1, 21):
                x = b.get("chara_id_%d" % i)
                if x and x != d["chara"]: ids.add(x)
        if ids:
            links = " &nbsp; ".join('<a href="char:%d" style="color:%s">%s</a>' % (c * 100 + 1, acc, h(self.win.db.names.get(c * 100 + 1, "chara %d" % c))) for c in sorted(ids))
            out += '<p style="color:%s">ตัวละครที่ได้รับโบนัสจากเนื้อเรื่องนี้ (chara_story_status): %s</p>' % (mute, links)
        return out


class Palette(QDialog):
    def __init__(self, win):
        super().__init__(win, Qt.Popup | Qt.FramelessWindowHint); self.win = win; self.setMinimumWidth(560); self.setObjectName("palette")
        self.setStyleSheet("QDialog#palette{background:%s;border:1px solid %s;border-radius:10px}" % (win.theme["panel"], win.theme["acc"]))
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)
        self.ed = QLineEdit(); self.ed.setPlaceholderText(tt("พิมพ์ชื่อตารางเพื่อกระโดดไป…  (Enter เปิด · Esc ปิด)", "Type a table name to jump to it…  (Enter to open · Esc to close)")); self.ed.setMinimumHeight(46)
        self.ed.setStyleSheet("font-size:15px;border-radius:0;border:0;border-bottom:1px solid %s;padding:6px 16px;background:%s;color:%s" % (win.theme["acc"], win.theme["panel2"], win.theme["ink"]))
        self.lst = QListWidget(); self.lst.setMinimumHeight(320)
        self.lst.setStyleSheet("QListWidget{background:%s;color:%s;border:0}QListWidget::item{padding:9px 16px;border-bottom:1px solid %s}"
                               "QListWidget::item:hover{background:%s}QListWidget::item:selected{background:%s;color:%s;border-left:3px solid %s}"
                               % (win.theme["panel"], win.theme["ink"], win.theme["line"], win.theme["panel2"], win.theme["accbg"], win.theme["ink"], win.theme["acc"])); lay.addWidget(self.ed); lay.addWidget(self.lst)
        self.ed.textChanged.connect(self.fill); self.lst.itemActivated.connect(self.go); self.lst.itemClicked.connect(self.go)

    def popup(self):
        self.ed.clear(); self.fill(); g = self.win.geometry(); self.move(g.center().x() - 280, g.top() + 110); self.show(); self.ed.setFocus()

    def fill(self):
        t = self.ed.text().lower().strip(); self.lst.clear()
        ts = [x for x in self.win.db.tables if t in x["name"].lower()]
        ts.sort(key=lambda x: (not x["name"].lower().startswith(t), x["name"] not in self.win.fav, x["name"]))
        from PySide6.QtWidgets import QListWidgetItem
        def add(text, data):
            it = QListWidgetItem(text); it.setData(Qt.UserRole, data); self.lst.addItem(it)
        if len(t) >= 2:
            ch = [i for i, n in self.win.db.names.items() if t in n.lower() or t == str(i)][:6]
            for i in ch: add(tt("🗺 ตัวละคร: %s  (%d)", "🗺 Character: %s  (%d)") % (self.win.db.names[i], i), ("char", i))
        for x in ts[:60]:
            add(("⭐ " if x["name"] in self.win.fav else "") + x["name"] + "      " + f"{x['rows']:,} " + tt("แถว", "rows"), ("table", x["name"]))
        if t: add(tt("🔎 ค้นหา “%s” ทั้งฐานข้อมูล", "🔎 Search “%s” in whole database") % self.ed.text().strip(), ("search", self.ed.text().strip()))
        if self.lst.count(): self.lst.setCurrentRow(0)

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Down, Qt.Key_Up):
            self.lst.setCurrentRow(max(0, min(self.lst.count() - 1, self.lst.currentRow() + (1 if e.key() == Qt.Key_Down else -1))))
        elif e.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.lst.currentItem(): self.go(self.lst.currentItem())
        else: super().keyPressEvent(e)

    def go(self, it):
        kind, val = it.data(Qt.UserRole); self.close()
        if kind == "search": self.win.open_search(val)
        elif kind == "char": self.win.open_char(val)
        else: self.win.open_table(val)


# ----------------------------------------------------------------------------- main window
class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.s = QSettings("DBExplorer", "DBExplorer")
        global LANG; LANG = "en" if str(self.s.value("lang", "th")) == "en" else "th"
        self.theme_name = self.s.value("theme", "dark"); self.theme = THEMES[self.theme_name]
        self.fav = list(self.s.value("fav", []) or []); self.recent = list(self.s.value("recent", []) or []); self.hist = list(self.s.value("hist", []) or [])
        if isinstance(self.fav, str): self.fav = [self.fav]
        self.db = DB(); self._tasks = []; self.pal = None
        self.setWindowTitle(APP); self.resize(1480, 880); self.setAcceptDrops(True)
        self.apply_theme()

        # header bar
        top = QFrame(); top.setObjectName("bar"); tl = QHBoxLayout(top); tl.setContentsMargins(16, 8, 16, 8)
        tl.addWidget(lbl("🗄️  DB Explorer", "logo")); self.chip = lbl(tt("ยังไม่ได้เปิดไฟล์", "No file opened"), mute=True); tl.addWidget(self.chip); tl.addStretch()
        for text, fn in ((tt("🔍 ค้นหาด่วน  Ctrl+K", "🔍 Quick find  Ctrl+K"), self.palette), ("🌓", self.toggle_theme), (tt("🌐 English", "🌐 ไทย"), self.switch_lang), (tt("📂 เปิดไฟล์  Ctrl+O", "📂 Open file  Ctrl+O"), self.open_dialog)):
            b = QPushButton(text); b.clicked.connect(fn); tl.addWidget(b)

        # sidebar
        side = QWidget(); sl = QVBoxLayout(side); sl.setContentsMargins(12, 12, 6, 8); sl.setSpacing(8)
        self.tq = QLineEdit(); self.tq.setPlaceholderText(tt("🔍 กรองชื่อตาราง…", "🔍 Filter table names…")); self.tq.textChanged.connect(self.fill_tree)
        r = QHBoxLayout(); self.he = QCheckBox(tt("ซ่อนตารางว่าง", "Hide empty tables")); self.he.setChecked(True); self.he.toggled.connect(self.fill_tree)
        self.ts = QComboBox(); self.ts.addItems([tt("ชื่อ A-Z", "Name A-Z"), tt("จำนวนแถว", "Row count")]); self.ts.currentIndexChanged.connect(self.fill_tree)
        r.addWidget(self.he); r.addStretch(); r.addWidget(self.ts)
        self.tc = lbl("", mute=True)
        self.tree = QTreeWidget(); self.tree.setHeaderHidden(True); self.tree.setIndentation(10); self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.itemDoubleClicked.connect(self.tree_open); self.tree.itemActivated.connect(self.tree_open); self.tree.customContextMenuRequested.connect(self.tree_menu)
        self.tree.itemClicked.connect(lambda it, c: it.childCount() == 0 and it.data(0, Qt.UserRole) and self.open_table(it.data(0, Qt.UserRole)))
        for w in (self.tq,): sl.addWidget(w)
        sl.addLayout(r); sl.addWidget(self.tc); sl.addWidget(self.tree, 1); side.setMinimumWidth(250); side.setMaximumWidth(420)

        self.tabs = QTabWidget(); self.tabs.setTabsClosable(True); self.tabs.setDocumentMode(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.home = HomeTab(self); self.chartab = CharTab(self); self.sqltab = SqlTab(self); self.searchtab = SearchTab(self)
        for w, n in ((self.home, tt("🏠 หน้าแรก", "🏠 Home")), (self.chartab, tt("🗺 แผนที่ตัวละคร", "🗺 Character map")), (self.sqltab, "⚡ SQL"), (self.searchtab, tt("🔎 ค้นทั้งฐานข้อมูล", "🔎 Search all"))):
            i = self.tabs.addTab(w, n); self.tabs.tabBar().setTabButton(i, self.tabs.tabBar().ButtonPosition.RightSide, None)

        split = QSplitter(); split.addWidget(side); split.addWidget(self.tabs); split.setStretchFactor(1, 1); split.setSizes([300, 1180])
        root = QWidget(); root.setObjectName("root"); rl = QVBoxLayout(root); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(0); rl.addWidget(top); rl.addWidget(split, 1)
        self.setCentralWidget(root)

        # detail dock
        self.dock = QDockWidget(tt("รายละเอียดแถว", "Row details"), self); self.dock.setFeatures(QDockWidget.DockWidgetClosable)
        self.dt = QTableWidget(0, 3); self.dt.setHorizontalHeaderLabels([tt("ฟิลด์", "Field"), tt("ค่า", "Value"), ""]); self.dt.verticalHeader().hide()
        self.dt.horizontalHeader().setStretchLastSection(False); self.dt.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.dt.setColumnWidth(0, 150); self.dt.setColumnWidth(2, 70); self.dt.setEditTriggers(QAbstractItemView.NoEditTriggers); self.dt.setWordWrap(True)
        self.dt.setAlternatingRowColors(True); self.dt.cellClicked.connect(self.copy_cell)
        dw = QWidget(); dl = QVBoxLayout(dw); dl.setContentsMargins(0, 0, 0, 0); dl.setSpacing(0)
        self.dbtn = QPushButton(tt("🗺 เปิดแผนที่ตัวละคร", "🗺 Open character map")); self.dbtn.setObjectName("pri"); self.dbtn.clicked.connect(self.dock_char); dl.addWidget(self.dbtn); dl.addWidget(self.dt)
        self.dock.setWidget(dw); self.addDockWidget(Qt.RightDockWidgetArea, self.dock); self.dock.setMinimumWidth(360); self.dock.hide()
        self.dcols, self.drow = [], []

        self.statusBar().showMessage(tt("พร้อมใช้งาน", "Ready"))
        for key, fn in (("Ctrl+K", self.palette), ("Ctrl+O", self.open_dialog), ("Ctrl+W", lambda: self.close_tab(self.tabs.currentIndex())), ("F5", self.reload)):
            QShortcut(QKeySequence(key), self, activated=fn)

    # --- helpers
    def keep(self, t):
        self._tasks = [x for x in self._tasks if x.isRunning()] + [t]

    def status(self, m): self.statusBar().showMessage(m, 6000)

    def icon_dir(self):
        """โฟลเดอร์ไอคอนสกิล (icon_skill_*.png): ที่ผู้ใช้เลือก → โฟลเดอร์ skill ข้างโปรแกรม"""
        if getattr(self, "_icondir", None) is not None: return self._icondir
        bases = [os.path.dirname(os.path.abspath(__file__)), os.path.dirname(os.path.abspath(sys.executable)), os.getcwd()]
        cands = [str(self.s.value("icondir", "") or "")] + [os.path.join(b, x) for b in bases for x in ("skill", os.path.join("skill", "skill"), "icons", "icon_skill")]
        self._icondir = ""
        for c in cands:
            if not c: continue
            for p in (c, os.path.join(c, "skill")):
                if os.path.isfile(os.path.join(p, "icon_skill_none.png")) or os.path.isfile(os.path.join(p, "icon_skill_1001.png")): self._icondir = p; return p
        return ""

    def icon_url(self, t):
        d = self.icon_dir()
        if not d: return ""
        for name in ("icon_skill_%s.png" % t, "icon_skill_none.png"):
            f = os.path.join(d, name)
            if os.path.isfile(f): return QUrl.fromLocalFile(f).toString()
        return ""

    def switch_lang(self):
        """สลับ TH/EN: สร้างหน้าต่างใหม่ด้วยภาษาใหม่ แล้วเปิดไฟล์/แท็บเดิมกลับมา"""
        global LANG
        names = [self.tabs.widget(i).name for i in range(FIXED, self.tabs.count()) if isinstance(self.tabs.widget(i), TableTab)]
        cur, geo, path = self.tabs.currentIndex(), self.geometry(), self.db.path
        sql, uid, recent = self.sqltab.ed.toPlainText(), self.chartab.uid, list(self.recent)
        LANG = "en" if LANG == "th" else "th"; self.s.setValue("lang", LANG)
        w = Main(); _WINDOWS.extend([w, self]); w.setGeometry(geo); w.show()
        if path:
            w.open_db(path)
            for n in names: w.open_table(n)
            w.recent = recent; w.s.setValue("recent", recent); w.home.refresh()
            if uid: w.chartab.show_uid(uid)
        if sql: w.sqltab.ed.setPlainText(sql)
        w.tabs.setCurrentIndex(cur if cur < FIXED else max(0, w.tabs.count() - 1))
        self.close()

    def apply_theme(self):
        QApplication.instance().setStyleSheet(QSS.format(**self.theme))

    def toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"; self.theme = THEMES[self.theme_name]
        self.s.setValue("theme", self.theme_name); self.apply_theme()
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if hasattr(w, "model"): w.model.theme = self.theme; w.model.layoutChanged.emit()
        self.sqltab.model.theme = self.theme; self.sqltab.model.layoutChanged.emit()
        self.pal = None
        if self.db.path: self.chartab.refresh_names()

    # --- database
    def open_dialog(self):
        p, _ = QFileDialog.getOpenFileName(self, tt("เลือกไฟล์ฐานข้อมูล SQLite", "Choose an SQLite database file"), self.s.value("lastdir", ""), tt("SQLite (*.db *.sqlite *.sqlite3 *.db3);;ทั้งหมด (*)", "SQLite (*.db *.sqlite *.sqlite3 *.db3);;All files (*)"))
        if p: self.open_db(p)

    def open_db(self, p):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.db.load(p)
        except Exception as e:
            QApplication.restoreOverrideCursor(); QMessageBox.warning(self, APP, str(e)); return
        QApplication.restoreOverrideCursor()
        self.s.setValue("last", p); self.s.setValue("lastdir", os.path.dirname(p))
        while self.tabs.count() > FIXED: self.tabs.removeTab(FIXED)
        self.chartab.refresh_names(); self.chartab.placeholder()
        self.recent = []; self.chip.setText(tt("%s  ·  %.1f MB  ·  %d ตาราง", "%s  ·  %.1f MB  ·  %d tables") % (os.path.basename(p), self.db.size / 1e6, len(self.db.tables))); self.chip.setToolTip(p)
        self.setWindowTitle("%s — %s" % (APP, os.path.basename(p)))
        self.fill_tree(); self.home.refresh(); self.tabs.setCurrentIndex(0); self.status(tt("เปิดแล้ว: ", "Opened: ") + p)

    def reload(self):
        if self.db.path: self.open_db(self.db.path)

    # --- tree
    def fill_tree(self, *_):
        qs = self.tq.text().lower().strip(); he = self.he.isChecked(); byrows = self.ts.currentIndex() == 1
        L = [t for t in self.db.tables if qs in t["name"].lower() and (not he or t["rows"] != 0)]
        cnt = {}
        for t in self.db.tables: cnt[t["name"].split("_")[0]] = cnt.get(t["name"].split("_")[0], 0) + 1
        groups = {}
        for t in L:
            p = t["name"].split("_")[0]; groups.setdefault(p if cnt[p] >= 4 else "_other", []).append(t)
        key = (lambda t: -t["rows"]) if byrows else (lambda t: t["name"])
        self.tree.clear()
        def mk(parent, t):
            it = QTreeWidgetItem(parent, [("★ " if t["name"] in self.fav else "") + t["name"] + "    " + f"{t['rows']:,}"])
            it.setData(0, Qt.UserRole, t["name"]); it.setToolTip(0, t["name"])
            if t["rows"] == 0: it.setForeground(0, QColor(self.theme["zero"]))
        favs = [t for t in L if t["name"] in self.fav]
        if favs and not qs:
            g = QTreeWidgetItem(self.tree, [tt("⭐ โปรด", "⭐ Favorites")]); g.setExpanded(True)
            for t in sorted(favs, key=key): mk(g, t)
        for gname in sorted(groups, key=lambda x: (x == "_other", x)):
            g = QTreeWidgetItem(self.tree, ["%s   (%d)" % (tt("อื่นๆ", "OTHER") if gname == "_other" else gname.upper(), len(groups[gname]))]); f = g.font(0); f.setBold(True); g.setFont(0, f)
            g.setForeground(0, QColor(self.theme["mute"]))
            for t in sorted(groups[gname], key=key): mk(g, t)
            g.setExpanded(bool(qs) or gname in ("unit", "skill"))
        self.tc.setText(tt("แสดง %d จาก %d ตาราง", "Showing %d of %d tables") % (len(L), len(self.db.tables)))

    def tree_open(self, it, *_):
        n = it.data(0, Qt.UserRole)
        if n: self.open_table(n)

    def tree_menu(self, pos):
        it = self.tree.itemAt(pos)
        if not it or not it.data(0, Qt.UserRole): return
        n = it.data(0, Qt.UserRole); m = QMenu(self)
        a1 = m.addAction(tt("เปิดตาราง", "Open table")); a2 = m.addAction(tt("☆ เอาออกจากรายการโปรด", "☆ Remove from favorites") if n in self.fav else tt("★ เพิ่มในรายการโปรด", "★ Add to favorites"))
        r = m.exec(self.tree.viewport().mapToGlobal(pos))
        if r == a1: self.open_table(n)
        elif r == a2:
            self.fav = [x for x in self.fav if x != n] if n in self.fav else [n] + self.fav
            self.s.setValue("fav", self.fav); self.fill_tree(); self.home.refresh()

    # --- tabs
    def find_tab(self, name):
        for i in range(FIXED, self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, TableTab) and w.name == name: return i
        return -1

    def open_table(self, name, filters=None, search=""):
        if not self.db.path: return
        i = self.find_tab(name) if not filters and not search else -1
        if i < 0:
            w = TableTab(self, name); w.selected.connect(self.on_selected)
            i = self.tabs.addTab(w, "📋 " + name); self.tabs.setTabToolTip(i, name)
            w.set_filters(filters or {}, search)
        self.tabs.setCurrentIndex(i)
        self.recent = [name] + [x for x in self.recent if x != name][:11]; self.s.setValue("recent", self.recent)

    def close_tab(self, i):
        if i >= FIXED: self.tabs.removeTab(i)

    def open_char(self, uid):
        self.tabs.setCurrentWidget(self.chartab); self.chartab.show_uid(int(uid))

    def open_sql(self, text):
        self.sqltab.ed.setPlainText(text); self.tabs.setCurrentWidget(self.sqltab)

    def open_search(self, text):
        self.searchtab.ed.setText(text); self.tabs.setCurrentWidget(self.searchtab); self.searchtab.go()

    def palette(self):
        if not self.db.path: return
        if not self.pal: self.pal = Palette(self)
        self.pal.popup()

    # --- detail dock
    def on_selected(self, cols, row):
        self.dcols, self.drow = cols, row
        if self.dock.isVisible(): self.fill_detail()

    def show_detail(self):
        self.dock.show(); w = self.tabs.currentWidget()
        if isinstance(w, TableTab): w.emit_sel()
        self.fill_detail()

    def fill_detail(self):
        t = self.dt; t.setRowCount(0); t.setRowCount(len(self.dcols))
        for i, (c, v) in enumerate(zip(self.dcols, self.drow)):
            t.setItem(i, 0, QTableWidgetItem(c)); t.item(i, 0).setForeground(QColor(self.theme["mute"]))
            s = "NULL" if v is None else ("[BLOB %d B]" % len(v) if isinstance(v, bytes) else str(v))
            if NAME_COL(c) and v in self.db.names: s += "   ·   " + self.db.names[v]
            it = QTableWidgetItem(s); it.setToolTip(tt("คลิกเพื่อคัดลอก", "Click to copy")); it.setData(Qt.UserRole, "" if v is None or isinstance(v, bytes) else str(v)); t.setItem(i, 1, it)
            if isinstance(v, int) and v != 0 and (re.search("id", c, re.I) or re.match(r"(action|depend_action|skill|unit|item|equip|enemy|wave|quest)", c, re.I)):
                b = QPushButton("🔗"); b.setToolTip(tt("ตามไปดูตารางอื่นที่ใช้ค่านี้", "Find other tables using this value")); b.setStyleSheet("padding:2px 6px;border-radius:6px")
                b.clicked.connect(lambda _=0, c=c, v=v, b=b: self.follow(c, v, b)); t.setCellWidget(i, 2, b)
            else: t.removeCellWidget(i, 2)
        t.resizeRowsToContents()

    def dock_char(self):
        d = dict(zip(self.dcols, self.drow)); u = d.get("unit_id")
        if u is None:
            for k, v in d.items():
                if NAME_COL(k) and isinstance(v, int): u = v
        if u: self.open_char(u)
        else: self.status(tt("แถวนี้ไม่มี unit_id", "This row has no unit_id"))

    def copy_cell(self, r, c):
        it = self.dt.item(r, 1)
        if c == 1 and it: QGuiApplication.clipboard().setText(it.data(Qt.UserRole)); self.status(tt("คัดลอกแล้ว", "Copied"))

    def follow(self, col, val, btn):
        refs = self.db.refs(col, val); m = QMenu(self)
        if not refs: m.addAction(tt("ไม่พบตารางอื่นที่มีค่านี้ในคอลัมน์ชื่อเดียวกัน", "No other table has this value in a same-named column")).setEnabled(False)
        else:
            m.addAction(tt("ตารางที่มี %s = %s", "Tables with %s = %s") % (col, val)).setEnabled(False); m.addSeparator()
            for n, c in refs: m.addAction("%s     (%d)" % (n, c)).setData(n)
        a = m.exec(btn.mapToGlobal(QPoint(0, btn.height())))
        if a and a.data(): self.open_table(a.data(), filters={col: "=" + str(val)})

    # --- drag & drop
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls(): e.acceptProposedAction()

    def dropEvent(self, e):
        for u in e.mimeData().urls():
            if u.isLocalFile(): self.open_db(u.toLocalFile()); break


def res_path(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def main():
    if sys.platform == "win32":  # ให้ไอคอนบน taskbar เป็นของโปรแกรมเอง ไม่ใช่ของ python
        try:
            import ctypes; ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("DBExplorer.Muimi")
        except Exception: pass
    app = QApplication(sys.argv); app.setApplicationName(APP)
    ico = res_path("muimi.ico")
    if os.path.isfile(ico): app.setWindowIcon(QIcon(ico))
    w = Main(); w.show()
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if path: w.open_db(path)
    else:
        last = w.s.value("last", "")
        if last and os.path.isfile(last): w.open_db(last)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
