
import math as _math
import numpy as _np
import pyaccel as _pyaccel


def calc_charge_loss_fraction_in_line(accmodel, **kwargs):
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
    accelerator, init_twiss, energy_spread, emittance, hmax, hmin, vmax, vmin = \
        _process_loss_fraction_args(accmodel, **kwargs)
    coupling = kwargs['global_coupling']

    if len(accelerator) == 0:
        accmodel.log('calc', '{}: charge_loss_fraction_in_line - accelerator length null!'.format(accmodel.prefix), c='red')
        loss_fraction = 0.0
        return (loss_fraction, _pyaccel.optics.TwissArray(init_twiss), None)

    try:
        twiss, m66 = _pyaccel.optics.calc_twiss(
            accelerator, init_twiss=init_twiss, indices='open')
        betax, etax = twiss.betax, twiss.etax
        betay, etay = twiss.betay, twiss.etay
        if _np.isnan(betax[-1]):
            accmodel.log('calc', '{}: charge_loss_fraction_in_line - beta NaN!'.format(accmodel.prefix), c='yellow')
            loss_fraction = 1.0
            return (loss_fraction, None, None)
    except (
            _np.linalg.linalg.LinAlgError, _pyaccel.optics.OpticsException,
            _pyaccel.tracking.TrackingException):
        accmodel.log('calc', '{}: charge_loss_fraction_in_line - unstable optics!'.format(accmodel.prefix), c='yellow')
        loss_fraction = 1.0
        return (loss_fraction, None, None)

    emitx = emittance * 1 / (1 + coupling)
    emity = emittance * coupling / (1 + coupling)
    sigmax = _np.sqrt(betax * emitx + (etax * energy_spread)**2)
    sigmay = _np.sqrt(betay * emity + (etay * energy_spread)**2)
    hmax[hmax > 1e100] = 1e100
    hmin[hmin < -1e100] = -1e100
    vmax[vmax > 1e100] = 1e100
    vmin[vmin < -1e100] = -1e100
    h_vc = hmax - hmin
    v_vc = vmax - vmin
    co = twiss.co
    rx, ry = co[0, :], co[2, :]
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
    min_xfrac_inf = _np.amin(xlim_inf/sigmax)
    min_xfrac_sup = _np.amin(xlim_sup/sigmax)
    min_yfrac_inf = _np.amin(ylim_inf/sigmay)
    min_yfrac_sup = _np.amin(ylim_sup/sigmay)
    sqrt2 = _np.sqrt(2)

    x_surviving_fraction = 0.5*_math.erf(min_xfrac_inf/sqrt2)
    x_surviving_fraction += 0.5*_math.erf(min_xfrac_sup/sqrt2)
    y_surviving_fraction = 0.5*_math.erf(min_yfrac_inf/sqrt2)
    y_surviving_fraction += 0.5*_math.erf(min_yfrac_sup/sqrt2)
    surviving_fraction = x_surviving_fraction * y_surviving_fraction
    loss_fraction = 1.0 - surviving_fraction
    return loss_fraction, twiss, m66


def calc_charge_loss_fraction_in_ring(accmodel, **kwargs):
    """Calculate charge loss in a ring.

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
    accelerator, init_twiss, energy_spread, emittance, hmax, hmin, vmax, vmin = \
        _process_loss_fraction_args(accmodel, **kwargs)
    init_pos = init_twiss.co

    if len(hmax) == len(accelerator):
        indices = 'open'
    elif len(hmax) == len(accelerator)+1:
        indices = 'closed'
    else:
        raise Exception(
            'Mismatch between size of accelerator object and size of '
            'vacuum chamber')

    try:
        twiss, *_ = _pyaccel.optics.calc_twiss(
            accelerator, init_twiss=init_twiss, indices=indices)
        betax, etax = twiss.betax, twiss.etax
        betay, etay = twiss.betay, twiss.etay
        if _np.isnan(betax[-1]):
            accmodel.log('calc', '{}: charge_loss_fraction_in_ring - beta NaN!'.format(accmodel.prefix), c='yellow')
            loss_fraction = 1.0
            return loss_fraction
    except (_np.linalg.linalg.LinAlgError, _pyaccel.optics.OpticsException,
            _pyaccel.tracking.TrackingException) as err:
        accmodel.log('calc', '{}: charge_loss_fraction_in_ring - unstable optics! ({})'.format(
            accmodel.prefix, str(err)), c='yellow')
        loss_fraction = 1.0
        return loss_fraction

    de = _np.linspace(-(3*energy_spread), (3*energy_spread), 21)
    de_probability = _np.zeros(len(de))
    lost_fraction = _np.zeros(len(de))
    total_lost_fraction = 0

    for i in range(len(de)):
        de_probability[i] = _np.exp(-(de[i]**2)/(2*(energy_spread**2)))/(_np.sqrt(2*_np.pi)*energy_spread)
        pos = [p for p in init_pos]
        pos[4] += de[i]
        orbit, *_ = _pyaccel.tracking.linepass(accelerator, pos, indices='open')
        if indices == 'closed':
            orb, *_ = _pyaccel.tracking.linepass(
                accelerator[-1:], particles=orbit[:, -1])
            orbit = _np.append(orbit, orb.transpose(), axis=1)

        if _np.isnan(orbit[0, -1]):
            lost_fraction[i] = 1.0
            total_lost_fraction += de_probability[i]*lost_fraction[i]
            continue

        rx, ry = orbit[[0, 2], :]
        xlim_inf, xlim_sup = rx - hmin, hmax - rx
        ylim_inf, ylim_sup = ry - vmin, vmax - ry
        xlim_inf[xlim_inf < 0] = 0
        xlim_sup[xlim_sup < 0] = 0
        ylim_inf[ylim_inf < 0] = 0
        ylim_sup[ylim_sup < 0] = 0
        emit_x_inf = (xlim_inf**2 - (etax*energy_spread)**2)/betax
        emit_x_sup = (xlim_sup**2 - (etax*energy_spread)**2)/betax
        emit_y_inf = (ylim_inf**2 - (etay*energy_spread)**2)/betay
        emit_y_sup = (ylim_sup**2 - (etay*energy_spread)**2)/betay
        emit_x_inf[emit_x_inf < 0] = 0.0
        emit_x_sup[emit_x_sup < 0] = 0.0
        emit_y_inf[emit_y_inf < 0] = 0.0
        emit_y_sup[emit_y_sup < 0] = 0.0
        min_emit_x = _np.amin([emit_x_inf, emit_x_sup])
        min_emit_y = _np.amin([emit_y_inf, emit_y_sup])
        min_emit = min_emit_x+min_emit_y if min_emit_x*min_emit_y !=0 else 0.0
        lf = _np.exp(-min_emit/emittance)
        lost_fraction[i] = lf if lf < 1 else 1.0
        total_lost_fraction += de_probability[i]*lost_fraction[i]

    total_lost_fraction = total_lost_fraction/_np.sum(de_probability)
    loss_fraction = total_lost_fraction if total_lost_fraction < 1.0 else 1.0
    return loss_fraction


def _process_loss_fraction_args(accmodel, **kwargs):
    
    accelerator = kwargs.get('accelerator', accmodel.accelerator)
    energy_spread = kwargs['energy_spread']
    emittance = kwargs['emittance']

    init_twiss = kwargs.get('twiss_at_entrance')
    init_twiss = kwargs.get('init_twiss', init_twiss)
    delta_rx = kwargs.get('delta_rx', 0.0)
    delta_angle = kwargs.get('delta_angle', 0.0)

    if isinstance(init_twiss, dict):
        init_twiss = _pyaccel.optics.Twiss.make_new(init_twiss)

    fixed_point = _transform_to_local_coordinates(
        accmodel, init_twiss.co, delta_rx, delta_angle)

    init_twiss.co = fixed_point

    if 'hmax' in kwargs and 'hmin' in kwargs:
        hmax = kwargs['hmax']
        hmin = kwargs['hmin']
    else:
        hmax = _np.array([ele.hmax for ele in accelerator])
        hmin = _np.array([ele.hmin for ele in accelerator])
    if 'vmax' in kwargs and 'vmin' in kwargs:
        vmax = kwargs['vmax']
        vmin = kwargs['vmin']
    else:
        vmax = _np.array([ele.vmax for ele in accelerator])
        vmin = _np.array([ele.vmin for ele in accelerator])
    return accelerator, init_twiss, energy_spread, emittance, hmax, hmin, vmax, vmin


def _transform_to_local_coordinates(accmodel,
    old_pos, delta_rx, delta_angle, delta_dl=0.0):

    accmodel.log('fix',
        '{}: fix _get_coordinate_system_parameters!'.format(accmodel.prefix), c='cyan')
    return old_pos

    # C, S = _np.cos(delta_angle), _np.sin(delta_angle)
    # old_angle = _np.arctan(old_pos[1])
    # new_pos = [p for p in old_pos]
    # new_pos[0] = C * old_pos[0] + S * old_pos[5] + delta_rx
    # new_pos[5] = -S * old_pos[0] + C * old_pos[5] + delta_dl
    # new_pos[1] = _np.arctan(delta_angle + old_angle)
    # return new_pos
