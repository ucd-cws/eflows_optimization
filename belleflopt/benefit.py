import functools

from matplotlib import pyplot as plt
import seaborn


class BenefitItem(object):

    _low_bound = None
    _high_bound = None

    # q1 -> q4 are calculated automatically whenever we set the margin
    _q1 = None
    _q2 = None
    _q3 = None
    _q4 = None
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

        if self._q2 <= value <= self._q3:  # if it's well in the window, benefit is 1
            # this check should be before the next one to account for always valid windows (ie, q1 == q2 and q3 == q4)
            return 1
        if value <= self._q1 or value >= self._q4:  # if it's way outside the window, benefit is 0
            return 0

        if self._q1 < value < self._q2:  # benefit for ramping up near low flow
            slope = 1 / (self._q2 - self._q1)
            return slope * (value - self._q1)
        else:  # only thing left is q3 < flow < q4 - benefit for ramping down at the high end of the box
            slope = 1 / (self._q4 - self._q3)
            return 1 - slope * (value - self._q3)


class BenefitBox(object):

    low_flow = None
    high_flow = None

    start_day_of_water_year = None
    end_day_of_water_year = None

    flow_item = None
    date_item = None

    def __init__(self, low_flow, high_flow, start_day_of_water_year, end_day_of_water_year):
        self.low_flow = low_flow
        self.high_flow = high_flow
        self.start_day_of_water_year = start_day_of_water_year
        self.end_day_of_water_year = end_day_of_water_year

    def single_flow_benefit(self, flow, day_of_year, flow_margin=0.1, date_margin=0.1):
        self.flow_item = BenefitItem()
        self.flow_item.low_bound = self.low_flow
        self.flow_item.high_bound = self.high_flow
        self.flow_item.margin = flow_margin

        self.date_item = BenefitItem()
        self.date_item.low_bound = self.start_day_of_water_year
        self.date_item.high_bound = self.end_day_of_water_year
        self.date_item.rollover = 365  # tell it that the last day of the year is equal to the first
        self.date_item.margin = date_margin

        return self.flow_item.single_value_benefit(value=flow, margin=flow_margin) * self.date_item.single_value_benefit(value=day_of_year, margin=date_margin)

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
        plt.scatter([self.flow_item._q1, self.flow_item._q2*self.date_item._q2, self.flow_item._q3*self.date_item._q3, self.flow_item._q4], [0, 1, 1, 0])

        # label the qs
        plt.text(self.flow_item._q1 + 6, -0.015, "q1", fontsize=9, fontstyle="italic")
        plt.text(self.flow_item._q2 - 19, 0.985, "q2", fontsize=9, fontstyle="italic")
        plt.text(self.flow_item._q3 + 6, 0.985, "q3", fontsize=9, fontstyle="italic")
        plt.text(self.flow_item._q4 - 19, -0.015, "q4", fontsize=9, fontstyle="italic")
        plt.show()
