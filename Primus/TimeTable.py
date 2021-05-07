# -*- coding: utf-8 -*-
"""
Created on Tue Apr 27 19:42:51 2021

@author: Nicolas

https://github.com/Gortaf
"""

class TimeTable():
    def __init__(self, raw_classes, raw_hours):
        """
        A class that symbolises a timetable, built from a specific session's
        hours.

        Parameters
        ----------
        raw_classes : list(str)
            the list of raw classes strings obtained from the browser
        raw_hours : list(list(str))
            the list of raw hours obtained from the browser

        """
        self.fully_known = True
        self.day_dic = {
            "Lun": list(),
            "Ma": list(),
            "Mer": list(),
            "J": list(),
            "V": list(),
            "S": list(),
            "D": list()
        }
        raw_classes = [class_name.split("\n")[0] for class_name in raw_classes]

        for class_day_hours in raw_hours:
            for day_hour in class_day_hours:
                splitted = day_hour.replace(" - ", " ").split(" ")
                if not any(day in day_hour for day in self.day_dic.keys()):
                    continue
                self.day_dic[splitted[0]].append(HourInterval(splitted[1], splitted[2]))

    def compatible_with(self, other):
        for self_day, other_day in zip(self.day_dic.values(), other.day_dic.values()):
            if len(self_day) == 0 or len(other_day) == 0:
                continue

            else:
                for self_hours in self_day:
                    for other_hours in other_day:
                        if self_hours.intersects(other_hours):
                            return False

        return True


    def __str__(self):
        ret = ""
        for day, hours in self.day_dic.items():
            ret += day+str([str(inter) for inter in hours])+"\n"

        return ret

class SectionTimeTable(TimeTable):
    def __init__(self, section_name, raw_hours):
        """
        A class that symbolises a timetable for a classe's section

        Parameters
        ----------
        section_name : str
            the section's name
        raw_hours : list(list(str))
            A list of list of strings, where each sublist contains 3 elements.
            The day, start hour and end hour
        """
        self.day_dic = {
            "Lun": list(),
            "Ma": list(),
            "Mer": list(),
            "J": list(),
            "V": list(),
            "S": list(),
            "D": list()
        }
        self.section_name = section_name
        self.fully_known = True
        for day_hour in raw_hours:
            # Skips string where a day isn't recognized
            if not any(day in day_hour for day in self.day_dic.keys()):
                self.fully_known = False
                continue
            try:
                self.day_dic[day_hour[0]].append(HourInterval(day_hour[1], day_hour[2]))
            except:
                self.fully_known = False

    def compatible_with(self, other):
        for self_day, other_day in zip(self.day_dic.values(), other.day_dic.values()):
            if len(self_day) == 0 or len(other_day) == 0:
                continue

            else:
                for self_hours in self_day:
                    for other_hours in other_day:
                        if self_hours.intersects(other_hours):
                            return False

        return True

class HourInterval():
    def __init__(self, hour_start, hour_end):
        self.hour_start = float(hour_start.replace(":","."))
        self.hour_end = float(hour_end.replace(":","."))

    def __str__(self):
        return f"{self.hour_start} - {self.hour_end}"

    def intersects(self, other):
        if self.hour_start > other.hour_end or self.hour_end < other.hour_start:
            return False
        else:
            return True

class TimeNode():
    def __init__(self, timetable, parent = None, childrens = list()):
        self.timetable = timetable
        self.parent = parent
        self.childrens = childrens
        if parent == None:
            self.depth = 0
        else:
            self.depth = parent.depth

    def check_compat_cascade(self, other):
        compat_result = self.timetable.compatible_with(other.timetable)
        if not compat_result:
            return False
        else:
            if self.parent == None:
                return True
            else:
                return self.parent.check_compat_cascade(other)

    def check_fully_known_cascade(self):
        if not self.timetable.fully_known:
            return False
        else:
            if self.parent == None:
                return True
            else:
                return self.parent.check_fully_known_cascade()

class TimeTree():
    def __init__(self, root_ttb):
        self.root = TimeNode(root_ttb)
        self.leafs = [self.root]
        self.new_leafs_buffer = []

    def extand(self, ttb_to_check):
        potential_node = TimeNode(ttb_to_check)
        to_return = False
        for leaf in iter(self.leafs):
            if leaf.check_compat_cascade(potential_node):
                leaf.childrens.append(potential_node)
                potential_node.parent = leaf
                self.new_leafs_buffer.append(potential_node)
                to_return = True

        return to_return

    def check_fully_known(self):
        for leaf in self.leafs:
            if leaf.check_fully_known_cascade():
                return True

        else:
            return False

    def commit_new_leafs(self):
        self.leafs = self.new_leafs_buffer
        self.new_leafs_buffer = list()

    def purify_leafs(self, expected_depth):
        for leaf in iter(self.leafs):
            if leaf.depth != expected_depth:
                self.leafs.remove(leaf)

class SynchroClass():
    def __init__(self, class_name, sections_timetable):
        self.class_name = class_name
        self.sections_timetable = sections_timetable
