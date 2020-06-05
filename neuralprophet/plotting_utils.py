import numpy as np
import pandas as pd

try:
    from matplotlib import pyplot as plt
    from matplotlib.dates import (
        MonthLocator,
        num2date,
        AutoDateLocator,
        AutoDateFormatter,
    )
    from matplotlib.ticker import FuncFormatter

    from pandas.plotting import deregister_matplotlib_converters
    deregister_matplotlib_converters()
except ImportError:
    print('Importing matplotlib failed. Plotting will not work.')


def set_y_as_percent(ax):
    """Set y axis as percentage

    Args:
        ax (matplotlib axis):

    Returns:
        ax
    """
    yticks = 100 * ax.get_yticks()
    yticklabels = ['{0:.4g}%'.format(y) for y in yticks]
    ax.set_yticklabels(yticklabels)
    return ax


def plot(fcst, ax=None,
         # uncertainty=True, plot_cap=True,
         xlabel='ds', ylabel='y',
         highlight_forecast=None,
         figsize=(10, 6),
         ):
    """Plot the NeuralProphet forecast

    Args:
        fcst (pd.DataFrame):  output of m.predict.
        ax (matplotlib axes):  on which to plot.
        xlabel (): label name on X-axis
        ylabel (): label name on Y-axis
        highlight_forecast ():
        figsize (): tuple width, height in inches.

    Returns:
        A matplotlib figure.
    """
    if ax is None:
        fig = plt.figure(facecolor='w', figsize=figsize)
        ax = fig.add_subplot(111)
    else:
        fig = ax.get_figure()
    ds = fcst['ds'].dt.to_pydatetime()

    yhat_col_names = [col_name for col_name in fcst.columns if 'yhat' in col_name]
    for i in range(len(yhat_col_names)):
        ax.plot(ds, fcst['yhat{}'.format(i + 1)], ls='-', c='#0072B2', alpha=0.2 + 2.0/(i+2.5))
        # Future Todo: use fill_between for all but highlight_forecast
        """
        col1 = 'yhat{}'.format(i+1)
        col2 = 'yhat{}'.format(i+2)
        no_na1 = fcst.copy()[col1].notnull().values
        no_na2 = fcst.copy()[col2].notnull().values
        no_na = [x1 and x2 for x1, x2 in zip(no_na1, no_na2)]
        fcst_na = fcst.copy()[no_na]
        fcst_na_t = fcst_na['ds'].dt.to_pydatetime()
        ax.fill_between(
            fcst_na_t,
            fcst_na[col1],
            fcst_na[col2],
            color='#0072B2', alpha=1.0/(i+1)
            )
        """
    if highlight_forecast is not None:
        ax.plot(ds, fcst['yhat{}'.format(highlight_forecast)], ls='-', c='b')
        ax.plot(ds, fcst['yhat{}'.format(highlight_forecast)], 'bx')

    ax.plot(ds, fcst['y'], 'k.')
    # just for debugging
    # ax.plot(ds, fcst['actual'], ls='-', c='r')

    # Future TODO: logistic/limited growth?
    """
    if 'cap' in fcst and plot_cap:
        ax.plot(ds, fcst['cap'], ls='--', c='k')
    if m.logistic_floor and 'floor' in fcst and plot_cap:
        ax.plot(ds, fcst['floor'], ls='--', c='k')
    if uncertainty and m.uncertainty_samples:
        ax.fill_between(ds, fcst['yhat_lower'], fcst['yhat_upper'],
                        color='#0072B2', alpha=0.2)
    """

    # Specify formatting to workaround matplotlib issue #12925
    locator = AutoDateLocator(interval_multiples=False)
    formatter = AutoDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    ax.grid(True, which='major', c='gray', ls='-', lw=1, alpha=0.2)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    fig.tight_layout()
    return fig


def plot_components(m,
                    fcst,
                    # uncertainty=False,
                    # plot_cap=True,
                    weekly_start=0,
                    yearly_start=0,
                    figsize=None,
                    ):
    """Plot the Prophet forecast components.

    Will plot whichever are available of: trend, holidays, weekly
    seasonality, yearly seasonality, and additive and multiplicative extra
    regressors.

    Parameters
    ----------
    m: Prophet model.
    fcst: pd.DataFrame output of m.predict.
    uncertainty: Optional boolean to plot uncertainty intervals, which will
        only be done if m.uncertainty_samples > 0.
    plot_cap: Optional boolean indicating if the capacity should be shown
        in the figure, if available.
    weekly_start: Optional int specifying the start day of the weekly
        seasonality plot. 0 (default) starts the week on Sunday. 1 shifts
        by 1 day to Monday, and so on.
    yearly_start: Optional int specifying the start day of the yearly
        seasonality plot. 0 (default) starts the year on Jan 1. 1 shifts
        by 1 day to Jan 2, and so on.
    figsize: Optional tuple width, height in inches.

    Returns
    -------
    A matplotlib figure.
    """
    # Identify components to be plotted
    components = ['trend']

    # Future TODO: Add Holidays
    # if m.train_holiday_names is not None and 'holidays' in fcst:
    #     components.append('holidays')

    ## Plot  seasonalities, if present
    if m.season_config is not None:
        if 'weekly' in m.season_config.periods:  # and 'weekly' in fcst:
            components.append('weekly')
        if  'yearly' in m.season_config.periods: # and 'yearly' in fcst:
            components.append('yearly')
        # # Other seasonalities
        # components.extend([name for name in sorted(m.seasonalities)
        #                     if name in fcst and name not in ['weekly', 'yearly']])

    # Future TODO: Add Regressors
    # regressors = {'additive': False, 'multiplicative': False}
    # for name, props in m.extra_regressors.items():
    #     regressors[props['mode']] = True
    # for mode in ['additive', 'multiplicative']:
    #     if regressors[mode] and 'extra_regressors_{}'.format(mode) in fcst:
    #         components.append('extra_regressors_{}'.format(mode))

    npanel = len(components)
    figsize = figsize if figsize else (9, 3 * npanel)
    fig, axes = plt.subplots(npanel, 1, facecolor='w', figsize=figsize)
    if npanel == 1:
        axes = [axes]
    # multiplicative_axes = []
    for ax, plot_name in zip(axes, components):
        if plot_name == 'trend':
            plot_forecast_component(
                fcst=fcst, name='trend', ax=ax,
                # uncertainty=uncertainty, plot_cap=plot_cap,
            )
        elif m.season_config is not None and plot_name in m.season_config.periods:
            if plot_name == 'weekly' or m.season_config.periods[plot_name]['period'] == 7:
                plot_weekly(m=m, name=plot_name, ax=ax, weekly_start=weekly_start, )
            if plot_name == 'yearly' or m.season_config.periods[plot_name]['period'] == 365.25:
                plot_yearly(m=m, name=plot_name, ax=ax, yearly_start=yearly_start, )
            # else:
            #     plot_seasonality(m=m, name=plot_name, ax=ax, uncertainty=uncertainty,)
        # elif plot_name in ['holidays', 'extra_regressors_additive', 'extra_regressors_multiplicative', ]:
        #     plot_forecast_component(m=m, fcst=fcst, name=plot_name, ax=ax, uncertainty=uncertainty, plot_cap=False, )
        # if plot_name in m.component_modes['multiplicative']:
        #     multiplicative_axes.append(ax)

    fig.tight_layout()
    # Reset multiplicative axes labels after tight_layout adjustment
    # for ax in multiplicative_axes:
    #     ax = set_y_as_percent(ax)
    return fig


def plot_forecast_component(fcst, name, ax=None, figsize=(10, 6)):
    # TODO: update docstring
    """Plot a particular component of the forecast.

    Parameters
    ----------
    m: Prophet model.
    fcst: pd.DataFrame output of m.predict.
    name: Name of the component to plot.
    ax: Optional matplotlib Axes to plot on.
    uncertainty: Optional boolean to plot uncertainty intervals, which will
        only be done if m.uncertainty_samples > 0.
    plot_cap: Optional boolean indicating if the capacity should be shown
        in the figure, if available.
    figsize: Optional tuple width, height in inches.

    Returns
    -------
    a list of matplotlib artists
    """
    artists = []
    if not ax:
        fig = plt.figure(facecolor='w', figsize=figsize)
        ax = fig.add_subplot(111)
    fcst_t = fcst['ds'].dt.to_pydatetime()
    artists += ax.plot(fcst_t, fcst[name], ls='-', c='#0072B2')
    # Specify formatting to workaround matplotlib issue #12925
    locator = AutoDateLocator(interval_multiples=False)
    formatter = AutoDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    ax.grid(True, which='major', c='gray', ls='-', lw=1, alpha=0.2)
    ax.set_xlabel('ds')
    ax.set_ylabel(name)
    # if name in m.component_modes['multiplicative']:
    #     ax = set_y_as_percent(ax)
    return artists



def plot_yearly(m, ax=None, yearly_start=0, figsize=(10, 6), name='yearly'):
    # TODO: update docstring
    """Plot the yearly component of the forecast.

    Parameters
    ----------
    m: Prophet model.
    ax: Optional matplotlib Axes to plot on. One will be created if
        this is not provided.
    uncertainty: Optional boolean to plot uncertainty intervals, which will
        only be done if m.uncertainty_samples > 0.
    yearly_start: Optional int specifying the start day of the yearly
        seasonality plot. 0 (default) starts the year on Jan 1. 1 shifts
        by 1 day to Jan 2, and so on.
    figsize: Optional tuple width, height in inches.
    name: Name of seasonality component if previously changed from default 'yearly'.

    Returns
    -------
    a list of matplotlib artists
    """
    artists = []
    if not ax:
        fig = plt.figure(facecolor='w', figsize=figsize)
        ax = fig.add_subplot(111)
    # Compute yearly seasonality for a Jan 1 - Dec 31 sequence of dates.
    days = (pd.date_range(start='2017-01-01', periods=365) +
            pd.Timedelta(days=yearly_start))
    df_y = pd.DataFrame({'ds': days, 'y': np.zeros_like(days)})
    seas = m.predict_seasonal_components(df_y)
    artists += ax.plot(
        df_y['ds'].dt.to_pydatetime(), seas[name], ls='-', c='#0072B2')
    ax.grid(True, which='major', c='gray', ls='-', lw=1, alpha=0.2)
    months = MonthLocator(range(1, 13), bymonthday=1, interval=2)
    ax.xaxis.set_major_formatter(FuncFormatter(
        lambda x, pos=None: '{dt:%B} {dt.day}'.format(dt=num2date(x))))
    ax.xaxis.set_major_locator(months)
    ax.set_xlabel('Day of year')
    ax.set_ylabel(name)
    if m.season_config.mode == 'multiplicative':
        ax = set_y_as_percent(ax)
    return artists


def plot_weekly(m, ax=None, weekly_start=0, figsize=(10, 6), name='weekly'):
    # TODO: update docstring
    """Plot the weekly component of the forecast.

    Parameters
    ----------
    m: Prophet model.
    ax: Optional matplotlib Axes to plot on. One will be created if this
        is not provided.
    uncertainty: Optional boolean to plot uncertainty intervals, which will
        only be done if m.uncertainty_samples > 0.
    weekly_start: Optional int specifying the start day of the weekly
        seasonality plot. 0 (default) starts the week on Sunday. 1 shifts
        by 1 day to Monday, and so on.
    figsize: Optional tuple width, height in inches.
    name: Name of seasonality component if changed from default 'weekly'.

    Returns
    -------
    a list of matplotlib artists
    """
    artists = []
    if not ax:
        fig = plt.figure(facecolor='w', figsize=figsize)
        ax = fig.add_subplot(111)
    # Compute weekly seasonality for a Sun-Sat sequence of dates.
    days = (pd.date_range(start='2017-01-01', periods=7) +
            pd.Timedelta(days=weekly_start))
    df_w = pd.DataFrame({'ds': days, 'y': np.zeros_like(days)})
    seas = m.predict_seasonal_components(df_w)
    days = days.day_name()
    artists += ax.plot(range(len(days)), seas[name], ls='-',
                    c='#0072B2')
    ax.grid(True, which='major', c='gray', ls='-', lw=1, alpha=0.2)
    ax.set_xticks(range(len(days)))
    ax.set_xticklabels(days)
    ax.set_xlabel('Day of week')
    ax.set_ylabel(name)
    if m.season_config.mode == 'multiplicative':
        ax = set_y_as_percent(ax)
    return artists
