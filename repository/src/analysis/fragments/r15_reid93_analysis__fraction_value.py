def fraction_value(n,d):
    return None if d==0 else dict(numerator=n,denominator=d,exact=str(Fraction(n,d)),value=float(Fraction(n,d)))
