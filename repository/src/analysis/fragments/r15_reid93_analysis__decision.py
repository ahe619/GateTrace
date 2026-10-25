def decision(report):
    agg=report['main']['aggregate'];seqs=report['main']['by_sequence']
    if any(u['final_events']==0 for u in [agg,*seqs.values()]):
        return dict(decision='TECHNICAL_STOP / INCONCLUSIVE',reason='identity precision undefined (N=0)',state='PENDING_CLAUDE_RECOMPUTE')
    def p(u):return Fraction(u['correct'],u['final_events'])
    safe={
        'all_high_ge_206':agg['bins']['high']['numerator']>=206,
        'all_precision_floor':p(agg)>=Fraction(14283,15850),
        '01_high_ge_12':seqs['MOT20-01']['bins']['high']['numerator']>=12,
        '02_high_ge_194':seqs['MOT20-02']['bins']['high']['numerator']>=194,
        '01_precision_floor':p(seqs['MOT20-01'])>=Fraction(509,550),
        '02_precision_floor':p(seqs['MOT20-02'])>=Fraction(26021,28950),
    }
    low={
        'all_low_ge_99':agg['bins']['low']['numerator']>=99,
        '01_low_ge_16':seqs['MOT20-01']['bins']['low']['numerator']>=16,
        '02_low_ge_70':seqs['MOT20-02']['bins']['low']['numerator']>=70,
    }
    delta=agg['bins']['low']['numerator']-84
    if not all(safe.values()):verdict='NOT_ADOPT / BASELINE_WITH_REGRESSION'
    elif delta<=-6:verdict='STOP_REPAIR_DIRECTION_FOR_THIS_CONFIGURATION'
    elif delta<=5:verdict='BASELINE_ONLY'
    elif delta<=14:verdict='DESCRIPTIVE_ONLY'
    elif not all(low.values()):verdict='DESCRIPTIVE_ONLY / SEQUENCE_DEPENDENT'
    else:verdict='CONTINUE_CANDIDATE'
    return dict(decision=verdict,state='PENDING_CLAUDE_RECOMPUTE',safety_checks=safe,low_checks=low,
        delta_low_correct=delta,exact_precision={k:fraction_value(u['correct'],u['final_events']) for k,u in [('ALL',agg),*seqs.items()]},
        thresholds=dict(all_precision='14283/15850',seq01_precision='509/550',seq02_precision='26021/28950'),
        rules_sha256=RULES_SHA,not_significance_test=True)
