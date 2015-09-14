
import math
import numpy
import pyaccel


def calc_charge_loss_fraction_in_line(accelerator, **kwargs):
    """Calculate charge loss in a line

    Keyword arguments:
    twiss_at_entrance -- Twiss parameters at the start of first element
    global_coupling   -- Global coupling
    energy_spread     -- Relative energy spread
    emittance         -- [m·rad]
    delta_rx          -- [m]
    delta_angle       -- [rad]
    hmax              -- [m]
    hmin              -- [m]
    vmax              -- [m]
    vmin              -- [m]
    """
    init_twiss, energy_spread, emittance, hmax, hmin, vmax, vmin = _process_loss_fraction_args(accelerator, **kwargs)
    coupling = kwargs['global_coupling']

    twiss, m66, transfer_matrices, orbit = pyaccel.optics.calc_twiss(accelerator, init_twiss = init_twiss)
    betax, etax, betay, etay = pyaccel.optics.get_twiss(twiss, ('betax','etax','betay','etay'))
    emitx = emittance * 1 / (1 + coupling)
    emity = emittance * coupling / (1 + coupling)
    sigmax = numpy.sqrt(betax * emitx + (etax * energy_spread)**2)
    sigmay = numpy.sqrt(betay * emity + (etax * energy_spread)**2)
    h_vc = hmax - hmin
    v_vc = vmax - vmin
    rx, ry = pyaccel.optics.get_twiss(twiss, ('rx','ry'))
    xlim_inf, xlim_sup = rx - hmin, hmax - rx
    ylim_inf, ylim_sup = ry - vmin, vmax - ry
    xlim_inf[xlim_inf < 0] = 0
    xlim_sup[xlim_sup < 0] = 0
    ylim_inf[ylim_inf < 0] = 0
    ylim_sup[ylim_sup < 0] = 0
    xlim_inf[xlim_inf > h_vc] = 0
    xlim_sup[xlim_sup > h_vc] = 0
    ylim_inf[ylim_inf > v_vc] = 0
    ylim_sup[ylim_sup > v_vc] = 0
    min_xfrac_inf = numpy.amin(xlim_inf/sigmax)
    min_xfrac_sup = numpy.amin(xlim_sup/sigmax)
    min_yfrac_inf = numpy.amin(ylim_inf/sigmay)
    min_yfrac_sup = numpy.amin(ylim_sup/sigmay)
    sqrt2 = math.sqrt(2)

    x_surviving_fraction = 0.5*math.erf(min_xfrac_inf/sqrt2) + \
                           0.5*math.erf(min_xfrac_sup/sqrt2)
    y_surviving_fraction = 0.5*math.erf(min_yfrac_inf/sqrt2) + \
                           0.5*math.erf(min_yfrac_sup/sqrt2)
    surviving_fraction = x_surviving_fraction * y_surviving_fraction
    loss_fraction = 1.0 - surviving_fraction
    return loss_fraction, twiss, m66, transfer_matrices, orbit


def calc_charge_loss_fraction_in_ring(accelerator, **kwargs):
    """Calculate charge loss in a ring

    Keyword arguments:
    twiss_at_entrance -- Twiss parameters at the start of first element
    energy_spread     -- Relative energy spread
    emittance         -- [m·rad]
    delta_rx          -- [m]
    delta_angle       -- [rad]
    hmax              -- [m]
    hmin              -- [m]
    vmax              -- [m]
    vmin              -- [m]
    """
    init_twiss, energy_spread, emittance, hmax, hmin, vmax, vmin = _process_loss_fraction_args(accelerator, **kwargs)

    init_pos = init_twiss.fixed_point

    try:
        twiss,*_ = pyaccel.optics.calc_twiss(accelerator, init_twiss = init_twiss)
        betax , betay, etax, etay = pyaccel.optics.get_twiss(twiss, ('betax', 'betay', 'etax', 'etay'))
        if math.isnan(betax[-1]):
            loss_fraction = 1.0
            return loss_fraction
    except (numpy.linalg.linalg.LinAlgError, pyaccel.optics.OpticsException,
            pyaccel.tracking.TrackingException):
        loss_fraction = 1.0
        return loss_fraction

    de = numpy.linspace(-(3*energy_spread), (3*energy_spread), 21)
    de_probability = numpy.zeros(len(de))
    lost_fraction = numpy.zeros(len(de))
    total_lost_fraction = 0

    for i in range(len(de)):
        de_probability[i] = math.exp(-(de[i]**2)/(2*(energy_spread**2)))/(math.sqrt(2*math.pi)*energy_spread)
        pos = [p for p in init_pos]
        pos[4] += de[i]
        orbit, *_ = pyaccel.tracking.linepass(accelerator, pos, indices = 'open')

        if math.isnan(orbit[0,-1]):
            lost_fraction[i] = 1.0
            total_lost_fraction += de_probability[i]*lost_fraction[i]
            continue

        rx, ry = orbit[[0,2],:]
        xlim_inf, xlim_sup = rx - hmin, hmax - rx
        ylim_inf, ylim_sup = ry - vmin, vmax - ry
        xlim_inf[xlim_inf < 0] = 0
        xlim_sup[xlim_sup < 0] = 0
        ylim_inf[ylim_inf < 0] = 0
        ylim_sup[ylim_sup < 0] = 0
        emit_x_inf = (xlim_inf**2  - (etax*energy_spread)**2)/betax
        emit_x_sup = (xlim_sup**2  - (etax*energy_spread)**2)/betax
        emit_y_inf = (ylim_inf**2  - (etay*energy_spread)**2)/betay
        emit_y_sup = (ylim_sup**2  - (etay*energy_spread)**2)/betay
        emit_x_inf[emit_x_inf < 0] = 0.0
        emit_x_sup[emit_x_sup < 0] = 0.0
        emit_y_inf[emit_y_inf < 0] = 0.0
        emit_y_sup[emit_y_sup < 0] = 0.0
        min_emit_x = numpy.amin([emit_x_inf, emit_x_sup])
        min_emit_y = numpy.amin([emit_y_inf, emit_y_sup])
        min_emit = min_emit_x + min_emit_y if min_emit_x*min_emit_y !=0 else 0.0
        lf = math.exp(-min_emit/emittance)
        lost_fraction[i] = lf if lf <1 else 1.0
        total_lost_fraction += de_probability[i]*lost_fraction[i]

    total_lost_fraction = total_lost_fraction/numpy.sum(de_probability)
    loss_fraction = total_lost_fraction if total_lost_fraction < 1.0 else 1.0
    return loss_fraction


def _process_loss_fraction_args(accelerator, **kwargs):
    energy_spread = kwargs['energy_spread']
    emittance     = kwargs['emittance']

    init_twiss = kwargs['init_twiss'] if 'init_twiss' in kwargs else kwargs['twiss_at_entrance']
    delta_rx = kwargs['delta_rx'] if 'delta_rx' in kwargs else 0.0
    delta_angle = kwargs['delta_angle'] if 'delta_angle' in kwargs else 0.0

    if isinstance(init_twiss, dict):
        init_twiss = pyaccel.optics.Twiss.make_new(init_twiss)
    init_twiss.fixed_point = _transform_to_local_coordinates(init_twiss.fixed_point, delta_rx, delta_angle)

    lattice = accelerator._accelerator.lattice
    if 'hmax' in kwargs and 'hmin' in kwargs:
        hmax = kwargs['hmax']
        hmin = kwargs['hmin']
    else:
        hmax, hmin = numpy.array([(lattice[i].hmax,lattice[i].hmin) for i in range(len(accelerator))]).transpose()
    if 'vmax' in kwargs and 'vmin' in kwargs:
        vmax = kwargs['vmax']
        vmin = kwargs['vmin']
    else:
        vmax, vmin = numpy.array([(lattice[i].vmax,lattice[i].vmin) for i in range(len(accelerator))]).transpose()
    return init_twiss, energy_spread, emittance, hmax, hmin, vmax, vmin


def _transform_to_local_coordinates(old_pos, delta_rx, delta_angle, delta_dl=0.0):
    C, S = math.cos(delta_angle), math.sin(delta_angle)
    old_angle = math.atan(old_pos[1])
    new_pos = [p for p in old_pos]
    new_pos[0] =  C * old_pos[0] + S * old_pos[5] + delta_rx
    new_pos[5] = -S * old_pos[0] + C * old_pos[5] + delta_dl
    new_pos[1] = math.tan(delta_angle + old_angle)
    return new_pos
