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
        # A dictionnary that will be filled with intervals of time
        # each key is a day (with the same syntax as on synchro)
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
                # Skips string where a day isn't recognized
                if not any(day in day_hour for day in self.day_dic.keys()):
                    continue
                splitted = day_hour.replace(" - ", " ").split(" ")
                self.day_dic[splitted[0]].append(HourInterval(splitted[1], splitted[2]))

    def __str__(self):
        ret = ""
        for day, hours in self.day_dic.items():
            ret += day+str([str(inter) for inter in hours])+"\n"

        return ret

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

