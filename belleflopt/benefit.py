import functools

import numpy
from matplotlib import pyplot as plt
import seaborn


class BenefitItem(object):
    """
        Could be the benefit on a day of the year or of a specific flow. Has a window of values
        and a margin over which benefit goes from 0-1 at the edges of those values. Calculates
        benefit for specific values based on this window and that margin. Abstracted here so
        that we can use if for dates or flows, but the locations of the "corners" still use
        the "q" terminology from the flows.
    """
    _low_bound = None
    _high_bound = None

    # q1 -> q4 are calculated automatically whenever we set the margin
    _q1 = None
    _q2 = None
    _q3 = None
    _q4 = None
    _q1_rollover = None
    _q2_rollover = None
    _q3_rollover = None
    _q4_rollover = None
    _margin = None
    rollover = None  # at what value should we consider it equivalent to 0?

    # using @properties for low_flow, high_flow, and margin so that we don't have to calculate q1->q4 every time we
    # check the benefit of something using this box. We can calculate those only on update of these parameters, then
    # just use them each time we check the benefit.
    @property
    def low_bound(self):
        return self._low_bound

    @low_bound.setter
    def low_bound(self, value):
        self._low_bound = value
        if self._high_bound is not None and self._margin is not None:
            self._update_qs()

    @property
    def high_bound(self):
        return self._high_bound

    @high_bound.setter
    def high_bound(self, value):
        self._high_bound = value
        if self._low_bound is not None and self._margin is not None:
            self._update_qs()

    @property
    def margin(self):
        return self._margin

    @margin.setter
    def margin(self, margin):
        if margin != self._margin:
            self._margin = margin
            if self._low_bound is not None and self._high_bound is not None:
                self._update_qs()

    def set_values(self, q1, q2, q3, q4):
        """
            Lets you explicitly set the q values if there is logic elsewhere that defines them
        :return:
        """
        self._q1 = q1
        self._q2 = q2
        self._q3 = q3
        self._q4 = q4

        self._check_rollover()

    def _check_rollover(self):
        """
            If any values go over the rollover, then modulos them back into the frame
        :return:
        """

        if self.rollover is None:
            return

        for item in ("_q2", "_q3", "_q4"):  # first, make sure the items are sequential by adding in the rollover value to anything coming in below the beginning
            if getattr(self, item) < self._q1:
                setattr(self, item, getattr(self, item) + self.rollover)  # this will get partially undone in the next block, but this way, we can use one set of logic no matter whether values are set manually and sequentially, or based on day of water year

        for item in ("_q1", "_q2", "_q3", "_q4"):
            setattr(self, "{}_rollover".format(item), getattr(self, item))
            setattr(self, item, int(getattr(self, item) % self.rollover))  # set each q to its modulo relative to 365

    def _update_qs(self):
        # otherwise, start constructing the window - find the size so we can build the ramping values.
        # see documentation for more description on how we build this
        window_size = self.high_bound - self.low_bound
        margin_size = int(self.margin * window_size)

        if self.rollover and self.high_bound == self.rollover and self.low_bound == 0:
            # if the upper bound is the same as the limit (the rollover value), and the low bound is 0, then make the edges square, because the benefit is always 1
            self._q3 = self._q4 = self.high_bound
            self._q1 = self._q2 = self.low_bound
            return

        self._q1 = self.low_bound - margin_size
        self._q2 = self.low_bound + margin_size
        self._q3 = self.high_bound - margin_size
        self._q4 = self.high_bound + margin_size

        self._check_rollover()

    def plot_window(self):
        """
            Provides the safe margins for plotting.
        :return:
        """

        if self.rollover is not None and self._q4 < self._q1:
            return 0, self.rollover

        buffer = int(abs(self._q4 - self._q1)/4)
        min_value = min(self._q1, self._q2, self._q3, self._q4)
        max_value = max(self._q1, self._q2, self._q3, self._q4)
        low_value = int(max(0, min_value - buffer))
        if self.rollover is not None:
            high_value = min(self.rollover, max_value + buffer)
        else:
            high_value = int(max_value + buffer)

        return low_value, high_value

    def single_value_benefit(self, value, margin):
        """
            Calculates the benefit of a single flow in relation to this box.
            We create 4 flow values with margins above and below the low and high flows.
            We then slope up to a benefit of 1 between the two lowflow points and down to a benefit of 0
            between the two highflow points.
        :param flow: The flow to get the benefit of
        :param flow_day: the day of water year for which this flow is allocated
        :param margin: a multiplier (between 0 and 1) for determining how much space to use for generating the slope
                        as we ramp up and down benefits. It would be best if margin was defined based upon the actual
                        statistical uncertainty of the bounding box
        :return: continuous 0-1 benefit of input flow
        """

        self.margin = margin  # set it this way, and it will recalculate q1 -> q4 only if it needs to

        value = value if not self.rollover or value >= self._q1 else value + self.rollover
        if self._q4 < self._q1:
            q1 = self._q1_rollover
            q2 = self._q2_rollover
            q3 = self._q3_rollover
            q4 = self._q4_rollover
        else:
            q1 = self._q1
            q2 = self._q2
            q3 = self._q3
            q4 = self._q4

        if q2 <= value <= q3:  # if it's well in the window, benefit is 1
            # this check should be before the next one to account for always valid windows (ie, q1 == q2 and q3 == q4)
            return 1
        if value <= q1 or value >= q4:  # if it's way outside the window, benefit is 0
            return 0

        if q1 < value < q2:  # benefit for ramping up near low flow
            slope = 1 / (q2 - q1)
            return slope * (value - q1)
        else:  # only thing left is q3 < flow < q4 - benefit for ramping down at the high end of the box
            slope = 1 / (q4 - q3)
            return 1 - slope * (value - q3)


class BenefitBox(object):

    low_flow = None
    high_flow = None

    start_day_of_water_year = None
    end_day_of_water_year = None

    flow_item = None
    date_item = None

    _annual_benefit = None

    def __init__(self, low_flow=None,
                 high_flow=None,
                 start_day_of_water_year=None,
                 end_day_of_water_year=None,
                 flow_margin=0.1,
                 date_margin=0.1,
                 component_name=None,
                 segment_id=None):

        self.component_name = component_name
        self.segment_id = segment_id

        self.low_flow = low_flow
        self.high_flow = high_flow
        self.start_day_of_water_year = start_day_of_water_year
        self.end_day_of_water_year = end_day_of_water_year

        self.flow_item = BenefitItem()
        self.flow_item.low_bound = self.low_flow
        self.flow_item.high_bound = self.high_flow
        self.flow_item.margin = flow_margin

        self.date_item = BenefitItem()
        self.date_item.low_bound = self.start_day_of_water_year
        self.date_item.high_bound = self.end_day_of_water_year
        self.date_item.rollover = 365  # tell it that the last day of the year is equal to the first
        self.date_item.margin = date_margin

    @property
    def name(self):
        return "Flow Component - Flow: ({}, {}), DOY: ({}, {})".format(self.low_flow,
                                                            self.high_flow,
                                                            self.start_day_of_water_year,
                                                            self.end_day_of_water_year,)

    def single_flow_benefit(self, flow, day_of_year, flow_margin=None, date_margin=None):
        if not flow_margin:
            flow_margin = self.flow_item.margin
        if not date_margin:
            date_margin = self.date_item.margin

        flow_benefit = self.flow_item.single_value_benefit(value=flow, margin=flow_margin)
        time_benefit = self.date_item.single_value_benefit(value=day_of_year, margin=date_margin)

        return float(flow_benefit) * time_benefit

    @property
    def annual_benefit(self):
        if self._annual_benefit is not None:
            return self._annual_benefit

        date_max = self.date_item.plot_window()[1]
        flow_max = self.flow_item.plot_window()[1]
        benefit_function = numpy.vectorize(self.single_flow_benefit, otypes=[float])
        days, flows = numpy.indices((date_max, flow_max))  # get the indices to pass through the vectorized function as flows and days
        self._annual_benefit = benefit_function(flows, days)
        return self._annual_benefit

    def plot_flow_benefit(self, min_flow=None, max_flow=None, day_of_year=100):

        # if they don't provide a min or max flow to plot, then set the values so that the box would be centered
        # with half the range on each side as 0s
        if not min_flow:
            min_flow = int(self.low_flow - (self.high_flow-self.low_flow)/2)
        if not max_flow:
            max_flow = int(self.high_flow + (self.high_flow-self.low_flow)/2)

        flows = range(min_flow, max_flow+1)

        # could also do this by just plotting (0,0) and the benefits at each q point, but this is easier to code
        benefits = map(functools.partial(self.single_flow_benefit, day_of_year=day_of_year), flows)

        plot = seaborn.lineplot(flows, benefits)
        plt.xlabel("Flow/Q (CFS)")
        plt.ylabel("Benefit")

        # add vertical lines for the low and high benefit flows
        plt.axvline(self.low_flow, 0, 1, dashes=(5, 8))
        plt.axvline(self.high_flow, 0, 1, dashes=(5, 8))

        # add points for the qs
        q2_benefit = self.single_flow_benefit(self.flow_item._q2, day_of_year=day_of_year)
        q3_benefit = self.single_flow_benefit(self.flow_item._q3, day_of_year=day_of_year)
        plt.scatter([self.flow_item._q1, self.flow_item._q2, self.flow_item._q3, self.flow_item._q4], [0, q2_benefit, q3_benefit, 0])

        # label the qs
        plt.text(self.flow_item._q1 + 6, -0.015, "q1", fontsize=9, fontstyle="italic")
        plt.text(self.flow_item._q2 - 19, q2_benefit - 0.015, "q2", fontsize=9, fontstyle="italic")
        plt.text(self.flow_item._q3 + 6, q3_benefit - 0.015, "q3", fontsize=9, fontstyle="italic")
        plt.text(self.flow_item._q4 - 19, -0.015, "q4", fontsize=9, fontstyle="italic")

        plt.ylim(-0.05, 1.05)
        plt.title("Benefit for {} on day {}".format(self.name, day_of_year))
        plt.show()

    def plot_annual_benefit(self):

        plt.imshow(numpy.swapaxes(self.annual_benefit, 0, 1),
                   cmap='viridis',
                   aspect="auto",  # allows it to fill the whole plot - by default keeps the axes on the same scale
                   vmin=0,  # force the data minimum to 0 - this should happen anyway, but let's be explicit
                   vmax=1,  # force the color scale to top out at 1, not at the data max
                   )
        plt.ylim(*self.flow_item.plot_window())
        plt.xlim(*self.date_item.plot_window())
        plt.title("Annual benefit for {} on segment {}".format(self.component_name, self.segment_id))
        plt.ylabel("Flow/Q (CFS)")
        plt.xlabel("Day of Water Year")
        plt.colorbar()
        plt.show()
