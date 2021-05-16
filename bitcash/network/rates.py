from collections import OrderedDict
from decimal import ROUND_DOWN
from functools import wraps
from time import time

import requests

from bitcash.utils import Decimal

DEFAULT_CACHE_TIME = 60

# Constant for use in deriving exchange
# rates when given in terms of 1 BCH.
ONE = Decimal(1)

# https://en.bitcoin.it/wiki/Units
SATOSHI = 1
uBCH = 10 ** 2
mBCH = 10 ** 5
BCH = 10 ** 8

SUPPORTED_CURRENCIES = OrderedDict(
    [
        ("satoshi", "Satoshi"),
        ("ubch", "Microbitcoincash"),
        ("mbch", "Millibitcoincash"),
        ("bch", "BitcoinCash"),
        ("usd", "United States Dollar"),
        ("eur", "Eurozone Euro"),
        ("gbp", "Pound Sterling"),
        ("jpy", "Japanese Yen"),
        ("cny", "Chinese Yuan"),
        ("cad", "Canadian Dollar"),
        ("aud", "Australian Dollar"),
        ("nzd", "New Zealand Dollar"),
        ("rub", "Russian Ruble"),
        ("brl", "Brazilian Real"),
        ("chf", "Swiss Franc"),
        ("sek", "Swedish Krona"),
        ("dkk", "Danish Krone"),
        ("isk", "Icelandic Krona"),
        ("pln", "Polish Zloty"),
        ("hkd", "Hong Kong Dollar"),
        ("krw", "South Korean Won"),
        ("sgd", "Singapore Dollar"),
        ("thb", "Thai Baht"),
        ("twd", "New Taiwan Dollar"),
        ("mxn", "Mexican Peso"),
        ("cop", "Colombian Peso"),
        ("ars", "Argentinian Peso"),
        ("cup", "Cuban Peso"),
        ("pen", "Peruvian Sol"),
        ("uyu", "Uruguayan Peso"),
        ("bob", "Bolivian Boliviano"),
        ("dop", "Dominican Peso"),
        ("clp", "Chilean Peso"),
        ("aed", "UAE Dirham"),
        ("afn", "Afghan Afghani"),
        ("all", "Albanian Lek"),
        ("amd", "Armenian Dram"),
        ("ang", "Netherlands Antillean Guilder"),
        ("aoa", "Angolan Kwanza"),
        ("awg", "Aruban Florin"),
        ("azn", "Azerbaijani Manat"),
        ("bam", "Bosnia-Herzegovina Convertible Mark"),
        ("bbd", "Barbadian Dollar"),
        ("bdt", "Bangladeshi Taka"),
        ("bgn", "Bulgarian Lev"),
        ("bhd", "Bahraini Dinar"),
        ("bif", "Burundian Franc"),
        ("bmd", "Bermudan Dollar"),
        ("bnd", "Brunei Dollar"),
        ("bsd", "Bahamian Dollar"),
        ("btn", "Bhutanese Ngultrum"),
        ("bwp", "Botswanan Pula"),
        ("byn", "Belarusian Ruble"),
        ("bzd", "Belize Dollar"),
        ("cdf", "Congolese Franc"),
        ("clf", "Chilean Unit of Account (UF)"),
        ("crc", "Costa Rican Colón"),
        ("cve", "Cape Verdean Escudo"),
        ("czk", "Czech Koruna"),
        ("djf", "Djiboutian Franc"),
        ("dzd", "Algerian Dinar"),
        ("egp", "Egyptian Pound"),
        ("etb", "Ethiopian Birr"),
        ("fjd", "Fijian Dollar"),
        ("fkp", "Falkland Islands Pound"),
        ("gel", "Georgian Lari"),
        ("ghs", "Ghanaian Cedi"),
        ("gip", "Gibraltar Pound"),
        ("gmd", "Gambian Dalasi"),
        ("gnf", "Guinean Franc"),
        ("gtq", "Guatemalan Quetzal"),
        ("gyd", "Guyanaese Dollar"),
        ("hnl", "Honduran Lempira"),
        ("hrk", "Croatian Kuna"),
        ("htg", "Haitian Gourde"),
        ("huf", "Hungarian Forint"),
        ("idr", "Indonesian Rupiah"),
        ("ils", "Israeli Shekel"),
        ("inr", "Indian Rupee"),
        ("iqd", "Iraqi Dinar"),
        ("irr", "Iranian Rial"),
        ("jmd", "Jamaican Dollar"),
        ("jod", "Jordanian Dinar"),
        ("kes", "Kenyan Shilling"),
        ("kgs", "Kyrgystani Som"),
        ("khr", "Cambodian Riel"),
        ("kmf", "Comorian Franc"),
        ("kpw", "North Korean Won"),
        ("kwd", "Kuwaiti Dinar"),
        ("kyd", "Cayman Islands Dollar"),
        ("kzt", "Kazakhstani Tenge"),
        ("lak", "Laotian Kip"),
        ("lbp", "Lebanese Pound"),
        ("lkr", "Sri Lankan Rupee"),
        ("lrd", "Liberian Dollar"),
        ("lsl", "Lesotho Loti"),
        ("lyd", "Libyan Dinar"),
        ("mad", "Moroccan Dirham"),
        ("mdl", "Moldovan Leu"),
        ("mkd", "Macedonian Denar"),
        ("mmk", "Myanma Kyat"),
        ("mnt", "Mongolian Tugrik"),
        ("mop", "Macanese Pataca"),
        ("mru", "Mauritanian Ouguiya"),
        ("mur", "Mauritian Rupee"),
        ("mvr", "Maldivian Rufiyaa"),
        ("mwk", "Malawian Kwacha"),
        ("myr", "Malaysian Ringgit"),
        ("mzn", "Mozambican Metical"),
        ("nad", "Namibian Dollar"),
        ("ngn", "Nigerian Naira"),
        ("nio", "Nicaraguan Córdoba"),
        ("nok", "Norwegian Krone"),
        ("npr", "Nepalese Rupee"),
        ("omr", "Omani Rial"),
        ("pab", "Panamanian Balboa"),
        ("pgk", "Papua New Guinean Kina"),
        ("php", "Philippine Peso"),
        ("pkr", "Pakistani Rupee"),
        ("pyg", "Paraguayan Guarani"),
        ("qar", "Qatari Rial"),
        ("ron", "Romanian Leu"),
        ("rsd", "Serbian Dinar"),
        ("rwf", "Rwandan Franc"),
        ("sar", "Saudi Riyal"),
        ("sbd", "Solomon Islands Dollar"),
        ("scr", "Seychellois Rupee"),
        ("sdg", "Sudanese Pound"),
        ("shp", "Saint Helena Pound"),
        ("sll", "Sierra Leonean Leone"),
        ("sos", "Somali Shilling"),
        ("srd", "Surinamese Dollar"),
        ("stn", "São Tomé and Príncipe Dobra"),
        ("svc", "Salvadoran Colón"),
        ("syp", "Syrian Pound"),
        ("szl", "Swazi Lilangeni"),
        ("tjs", "Tajikistani Somoni"),
        ("tmt", "Turkmenistani Manat"),
        ("tnd", "Tunisian Dinar"),
        ("top", "Tongan Paʻanga"),
        ("try", "Turkish Lira"),
        ("ttd", "Trinidad and Tobago Dollar"),
        ("tzs", "Tanzanian Shilling"),
        ("uah", "Ukrainian Hryvnia"),
        ("ugx", "Ugandan Shilling"),
        ("uzs", "Uzbekistan Som"),
        ("ves", "Venezuelan Bolívar Soberano"),
        ("vnd", "Vietnamese Dong"),
        ("vuv", "Vanuatu Vatu"),
        ("wst", "Samoan Tala"),
        ("xaf", "CFA Franc BEAC"),
        ("xcd", "East Caribbean Dollar"),
        ("xof", "CFA Franc BCEAO"),
        ("xpf", "CFP Franc"),
        ("yer", "Yemeni Rial"),
        ("zar", "South African Rand"),
        ("zmw", "Zambian Kwacha"),
        ("zwl", "Zimbabwean Dollar"),
    ]
)

# https://en.wikipedia.org/wiki/ISO_4217
CURRENCY_PRECISION = {
    "satoshi": 0,
    "ubch": 2,
    "mbch": 5,
    "bch": 8,
    "usd": 2,
    "eur": 2,
    "gbp": 2,
    "jpy": 0,
    "cny": 2,
    "cad": 2,
    "aud": 2,
    "nzd": 2,
    "rub": 2,
    "brl": 2,
    "chf": 2,
    "sek": 2,
    "dkk": 2,
    "isk": 2,
    "pln": 2,
    "hkd": 2,
    "krw": 0,
    "sgd": 2,
    "thb": 2,
    "twd": 2,
    "mxn": 2,
    "cop": 0,
    "ars": 2,
    "cup": 2,
    "pen": 2,
    "uyu": 2,
    "bob": 2,
    "dop": 2,
    "clp": 0,
    "aed": 2,
    "afn": 2,
    "all": 2,
    "amd": 2,
    "ang": 2,
    "aoa": 2,
    "awg": 2,
    "azn": 2,
    "bam": 2,
    "bbd": 2,
    "bdt": 2,
    "bgn": 2,
    "bhd": 3,
    "bif": 0,
    "bmd": 2,
    "bnd": 2,
    "bsd": 2,
    "btn": 2,
    "bwp": 2,
    "byn": 2,
    "bzd": 2,
    "cdf": 2,
    "clf": 4,
    "crc": 2,
    "cve": 2,
    "czk": 2,
    "djf": 0,
    "dzd": 2,
    "egp": 2,
    "etb": 2,
    "fjd": 2,
    "fkp": 2,
    "gel": 2,
    "ghs": 2,
    "gip": 2,
    "gmd": 2,
    "gnf": 0,
    "gtq": 2,
    "gyd": 2,
    "hnl": 2,
    "hrk": 2,
    "htg": 2,
    "huf": 2,
    "idr": 2,
    "ils": 2,
    "inr": 2,
    "iqd": 3,
    "irr": 2,
    "jmd": 2,
    "jod": 3,
    "kes": 2,
    "kgs": 2,
    "khr": 2,
    "kmf": 0,
    "kpw": 2,
    "kwd": 3,
    "kyd": 2,
    "kzt": 2,
    "lak": 2,
    "lbp": 2,
    "lkr": 2,
    "lrd": 2,
    "lsl": 2,
    "lyd": 3,
    "mad": 2,
    "mdl": 2,
    "mkd": 2,
    "mmk": 2,
    "mnt": 2,
    "mop": 2,
    "mru": 2,
    "mur": 2,
    "mvr": 2,
    "mwk": 2,
    "myr": 2,
    "mzn": 2,
    "nad": 2,
    "ngn": 2,
    "nio": 2,
    "nok": 2,
    "npr": 2,
    "omr": 3,
    "pab": 2,
    "pgk": 2,
    "php": 2,
    "pkr": 2,
    "pyg": 0,
    "qar": 2,
    "ron": 2,
    "rsd": 2,
    "rwf": 0,
    "sar": 2,
    "sbd": 2,
    "scr": 2,
    "sdg": 2,
    "shp": 2,
    "sll": 2,
    "sos": 2,
    "srd": 2,
    "stn": 2,
    "svc": 2,
    "syp": 2,
    "szl": 2,
    "tjs": 2,
    "tmt": 2,
    "tnd": 3,
    "top": 2,
    "try": 2,
    "ttd": 2,
    "tzs": 2,
    "uah": 2,
    "ugx": 0,
    "uzs": 2,
    "ves": 2,
    "vnd": 0,
    "vuv": 0,
    "wst": 2,
    "xaf": 0,
    "xcd": 2,
    "xof": 0,
    "xpf": 0,
    "yer": 2,
    "zar": 2,
    "zmw": 2,
    "zwl": 2,
}


def set_rate_cache_time(seconds):
    global DEFAULT_CACHE_TIME
    DEFAULT_CACHE_TIME = seconds


def satoshi_to_satoshi():
    return SATOSHI


def ubch_to_satoshi():
    return uBCH


def mbch_to_satoshi():
    return mBCH


def bch_to_satoshi():
    return BCH


class BitpayRates:
    """
    API Documentation:
    https://bitpay.com/api/rates#rest-api-resources-rates
    """

    SINGLE_RATE = "https://bitpay.com/rates/BCH/"

    @classmethod
    def currency_to_satoshi(cls, currency):
        headers = {"x-accept-version": "2.0.0", "Accept": "application/json"}
        r = requests.get(cls.SINGLE_RATE + currency, headers=headers)
        r.raise_for_status()
        rate = r.json()["data"]["rate"]
        return int(ONE / Decimal(rate) * BCH)

    @classmethod
    def usd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("usd")

    @classmethod
    def eur_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("eur")

    @classmethod
    def gbp_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("gbp")

    @classmethod
    def jpy_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("jpy")

    @classmethod
    def cny_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("cny")

    @classmethod
    def hkd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("hkd")

    @classmethod
    def cad_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("cad")

    @classmethod
    def aud_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("aud")

    @classmethod
    def nzd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("nzd")

    @classmethod
    def rub_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("rub")

    @classmethod
    def brl_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("brl")

    @classmethod
    def chf_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("chf")

    @classmethod
    def sek_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("sek")

    @classmethod
    def dkk_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("dkk")

    @classmethod
    def isk_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("isk")

    @classmethod
    def pln_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("pln")

    @classmethod
    def krw_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("krw")

    @classmethod
    def twd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("twd")

    @classmethod
    def mxn_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("mxn")

    @classmethod
    def ars_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("ars")

    @classmethod
    def cop_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("cop")

    @classmethod
    def cup_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("cup")

    @classmethod
    def pen_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("pen")

    @classmethod
    def uyu_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("uyu")

    @classmethod
    def clp_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("clp")

    @classmethod
    def sgd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("sgd")

    @classmethod
    def thb_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("thb")

    @classmethod
    def bob_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("bob")

    @classmethod
    def dop_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("dop")

    @classmethod
    def aed_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("aed")

    @classmethod
    def afn_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("afn")

    @classmethod
    def all_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("all")

    @classmethod
    def amd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("amd")

    @classmethod
    def ang_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("ang")

    @classmethod
    def aoa_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("aoa")

    @classmethod
    def awg_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("awg")

    @classmethod
    def azn_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("azn")

    @classmethod
    def bam_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("bam")

    @classmethod
    def bbd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("bbd")

    @classmethod
    def bdt_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("bdt")

    @classmethod
    def bgn_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("bgn")

    @classmethod
    def bhd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("bhd")

    @classmethod
    def bif_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("bif")

    @classmethod
    def bmd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("bmd")

    @classmethod
    def bnd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("bnd")

    @classmethod
    def bsd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("bsd")

    @classmethod
    def btn_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("btn")

    @classmethod
    def bwp_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("bwp")

    @classmethod
    def byn_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("byn")

    @classmethod
    def bzd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("bzd")

    @classmethod
    def cdf_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("cdf")

    @classmethod
    def clf_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("clf")

    @classmethod
    def crc_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("crc")

    @classmethod
    def cve_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("cve")

    @classmethod
    def czk_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("czk")

    @classmethod
    def djf_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("djf")

    @classmethod
    def dzd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("dzd")

    @classmethod
    def egp_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("egp")

    @classmethod
    def etb_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("etb")

    @classmethod
    def fjd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("fjd")

    @classmethod
    def fkp_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("fkp")

    @classmethod
    def gel_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("gel")

    @classmethod
    def ghs_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("ghs")

    @classmethod
    def gip_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("gip")

    @classmethod
    def gmd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("gmd")

    @classmethod
    def gnf_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("gnf")

    @classmethod
    def gtq_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("gtq")

    @classmethod
    def gyd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("gyd")

    @classmethod
    def hnl_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("hnl")

    @classmethod
    def hrk_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("hrk")

    @classmethod
    def htg_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("htg")

    @classmethod
    def huf_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("huf")

    @classmethod
    def idr_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("idr")

    @classmethod
    def ils_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("ils")

    @classmethod
    def inr_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("inr")

    @classmethod
    def iqd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("iqd")

    @classmethod
    def irr_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("irr")

    @classmethod
    def jmd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("jmd")

    @classmethod
    def jod_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("jod")

    @classmethod
    def kes_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("kes")

    @classmethod
    def kgs_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("kgs")

    @classmethod
    def khr_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("khr")

    @classmethod
    def kmf_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("kmf")

    @classmethod
    def kpw_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("kpw")

    @classmethod
    def kwd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("kwd")

    @classmethod
    def kyd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("kyd")

    @classmethod
    def kzt_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("kzt")

    @classmethod
    def lak_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("lak")

    @classmethod
    def lbp_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("lbp")

    @classmethod
    def lkr_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("lkr")

    @classmethod
    def lrd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("lrd")

    @classmethod
    def lsl_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("lsl")

    @classmethod
    def lyd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("lyd")

    @classmethod
    def mad_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("mad")

    @classmethod
    def mdl_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("mdl")

    @classmethod
    def mkd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("mkd")

    @classmethod
    def mmk_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("mmk")

    @classmethod
    def mnt_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("mnt")

    @classmethod
    def mop_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("mop")

    @classmethod
    def mru_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("mru")

    @classmethod
    def mur_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("mur")

    @classmethod
    def mvr_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("mvr")

    @classmethod
    def mwk_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("mwk")

    @classmethod
    def myr_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("myr")

    @classmethod
    def mzn_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("mzn")

    @classmethod
    def nad_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("nad")

    @classmethod
    def ngn_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("ngn")

    @classmethod
    def nio_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("nio")

    @classmethod
    def nok_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("nok")

    @classmethod
    def npr_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("npr")

    @classmethod
    def omr_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("omr")

    @classmethod
    def pab_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("pab")

    @classmethod
    def pgk_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("pgk")

    @classmethod
    def php_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("php")

    @classmethod
    def pkr_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("pkr")

    @classmethod
    def pyg_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("pyg")

    @classmethod
    def qar_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("qar")

    @classmethod
    def ron_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("ron")

    @classmethod
    def rsd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("rsd")

    @classmethod
    def rwf_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("rwf")

    @classmethod
    def sar_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("sar")

    @classmethod
    def sbd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("sbd")

    @classmethod
    def scr_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("scr")

    @classmethod
    def sdg_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("sdg")

    @classmethod
    def shp_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("shp")

    @classmethod
    def sll_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("sll")

    @classmethod
    def sos_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("sos")

    @classmethod
    def srd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("srd")

    @classmethod
    def stn_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("stn")

    @classmethod
    def svc_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("svc")

    @classmethod
    def syp_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("syp")

    @classmethod
    def szl_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("szl")

    @classmethod
    def tjs_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("tjs")

    @classmethod
    def tmt_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("tmt")

    @classmethod
    def tnd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("tnd")

    @classmethod
    def top_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("top")

    @classmethod
    def try_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("try")

    @classmethod
    def ttd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("ttd")

    @classmethod
    def tzs_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("tzs")

    @classmethod
    def uah_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("uah")

    @classmethod
    def ugx_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("ugx")

    @classmethod
    def uzs_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("uzs")

    @classmethod
    def ves_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("ves")

    @classmethod
    def vnd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("vnd")

    @classmethod
    def vuv_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("vuv")

    @classmethod
    def wst_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("wst")

    @classmethod
    def xaf_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("xaf")

    @classmethod
    def xcd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("xcd")

    @classmethod
    def xof_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("xof")

    @classmethod
    def xpf_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("xpf")

    @classmethod
    def yer_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("yer")

    @classmethod
    def zar_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("zar")

    @classmethod
    def zmw_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("zmw")

    @classmethod
    def zwl_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("zwl")



class CoinbaseRates:
    """
    API Documentation:
    https://developers.coinbase.com/api/v2#get-currencies
    """

    SINGLE_RATE = "https://api.coinbase.com/v2/exchange-rates?currency=BCH"

    @classmethod
    def currency_to_satoshi(cls, currency):
        r = requests.get(cls.SINGLE_RATE.format(currency))
        r.raise_for_status()
        rate = r.json()["data"]["rates"][currency]
        return int(ONE / Decimal(rate) * BCH)

    @classmethod
    def usd_to_satoshi(cls):  # pragma: no cover
        return cls.currency_to_satoshi("USD")


class RatesAPI:
    """Each method converts exactly 1 unit of the currency to the equivalent
    number of satoshi.
    """

    IGNORED_ERRORS = (
        requests.exceptions.ConnectionError,
        requests.exceptions.HTTPError,
        requests.exceptions.Timeout,
    )

    USD_RATES = [BitpayRates.usd_to_satoshi, CoinbaseRates.usd_to_satoshi]
    EUR_RATES = [BitpayRates.eur_to_satoshi]
    GBP_RATES = [BitpayRates.gbp_to_satoshi]
    JPY_RATES = [BitpayRates.jpy_to_satoshi]
    CNY_RATES = [BitpayRates.cny_to_satoshi]
    HKD_RATES = [BitpayRates.hkd_to_satoshi]
    CAD_RATES = [BitpayRates.cad_to_satoshi]
    AUD_RATES = [BitpayRates.aud_to_satoshi]
    NZD_RATES = [BitpayRates.nzd_to_satoshi]
    RUB_RATES = [BitpayRates.rub_to_satoshi]
    BRL_RATES = [BitpayRates.brl_to_satoshi]
    CHF_RATES = [BitpayRates.chf_to_satoshi]
    SEK_RATES = [BitpayRates.sek_to_satoshi]
    DKK_RATES = [BitpayRates.dkk_to_satoshi]
    ISK_RATES = [BitpayRates.isk_to_satoshi]
    PLN_RATES = [BitpayRates.pln_to_satoshi]
    KRW_RATES = [BitpayRates.krw_to_satoshi]
    CLP_RATES = [BitpayRates.clp_to_satoshi]
    SGD_RATES = [BitpayRates.sgd_to_satoshi]
    THB_RATES = [BitpayRates.thb_to_satoshi]
    TWD_RATES = [BitpayRates.twd_to_satoshi]
    MXN_RATES = [BitpayRates.mxn_to_satoshi]
    ARS_RATES = [BitpayRates.ars_to_satoshi]
    COP_RATES = [BitpayRates.cop_to_satoshi]
    CUP_RATES = [BitpayRates.cup_to_satoshi]
    PEN_RATES = [BitpayRates.pen_to_satoshi]
    UYU_RATES = [BitpayRates.uyu_to_satoshi]
    BOB_RATES = [BitpayRates.bob_to_satoshi]
    DOP_RATES = [BitpayRates.dop_to_satoshi]
    AED_RATES = [BitpayRates.aed_to_satoshi]
    AFN_RATES = [BitpayRates.afn_to_satoshi]
    ALL_RATES = [BitpayRates.all_to_satoshi]
    AMD_RATES = [BitpayRates.amd_to_satoshi]
    ANG_RATES = [BitpayRates.ang_to_satoshi]
    AOA_RATES = [BitpayRates.aoa_to_satoshi]
    AWG_RATES = [BitpayRates.awg_to_satoshi]
    AZN_RATES = [BitpayRates.azn_to_satoshi]
    BAM_RATES = [BitpayRates.bam_to_satoshi]
    BBD_RATES = [BitpayRates.bbd_to_satoshi]
    BDT_RATES = [BitpayRates.bdt_to_satoshi]
    BGN_RATES = [BitpayRates.bgn_to_satoshi]
    BHD_RATES = [BitpayRates.bhd_to_satoshi]
    BIF_RATES = [BitpayRates.bif_to_satoshi]
    BMD_RATES = [BitpayRates.bmd_to_satoshi]
    BND_RATES = [BitpayRates.bnd_to_satoshi]
    BSD_RATES = [BitpayRates.bsd_to_satoshi]
    BTN_RATES = [BitpayRates.btn_to_satoshi]
    BWP_RATES = [BitpayRates.bwp_to_satoshi]
    BYN_RATES = [BitpayRates.byn_to_satoshi]
    BZD_RATES = [BitpayRates.bzd_to_satoshi]
    CDF_RATES = [BitpayRates.cdf_to_satoshi]
    CLF_RATES = [BitpayRates.clf_to_satoshi]
    CRC_RATES = [BitpayRates.crc_to_satoshi]
    CVE_RATES = [BitpayRates.cve_to_satoshi]
    CZK_RATES = [BitpayRates.czk_to_satoshi]
    DJF_RATES = [BitpayRates.djf_to_satoshi]
    DZD_RATES = [BitpayRates.dzd_to_satoshi]
    EGP_RATES = [BitpayRates.egp_to_satoshi]
    ETB_RATES = [BitpayRates.etb_to_satoshi]
    FJD_RATES = [BitpayRates.fjd_to_satoshi]
    FKP_RATES = [BitpayRates.fkp_to_satoshi]
    GEL_RATES = [BitpayRates.gel_to_satoshi]
    GHS_RATES = [BitpayRates.ghs_to_satoshi]
    GIP_RATES = [BitpayRates.gip_to_satoshi]
    GMD_RATES = [BitpayRates.gmd_to_satoshi]
    GNF_RATES = [BitpayRates.gnf_to_satoshi]
    GTQ_RATES = [BitpayRates.gtq_to_satoshi]
    GYD_RATES = [BitpayRates.gyd_to_satoshi]
    HNL_RATES = [BitpayRates.hnl_to_satoshi]
    HRK_RATES = [BitpayRates.hrk_to_satoshi]
    HTG_RATES = [BitpayRates.htg_to_satoshi]
    HUF_RATES = [BitpayRates.huf_to_satoshi]
    IDR_RATES = [BitpayRates.idr_to_satoshi]
    ILS_RATES = [BitpayRates.ils_to_satoshi]
    INR_RATES = [BitpayRates.inr_to_satoshi]
    IQD_RATES = [BitpayRates.iqd_to_satoshi]
    IRR_RATES = [BitpayRates.irr_to_satoshi]
    JMD_RATES = [BitpayRates.jmd_to_satoshi]
    JOD_RATES = [BitpayRates.jod_to_satoshi]
    KES_RATES = [BitpayRates.kes_to_satoshi]
    KGS_RATES = [BitpayRates.kgs_to_satoshi]
    KHR_RATES = [BitpayRates.khr_to_satoshi]
    KMF_RATES = [BitpayRates.kmf_to_satoshi]
    KPW_RATES = [BitpayRates.kpw_to_satoshi]
    KWD_RATES = [BitpayRates.kwd_to_satoshi]
    KYD_RATES = [BitpayRates.kyd_to_satoshi]
    KZT_RATES = [BitpayRates.kzt_to_satoshi]
    LAK_RATES = [BitpayRates.lak_to_satoshi]
    LBP_RATES = [BitpayRates.lbp_to_satoshi]
    LKR_RATES = [BitpayRates.lkr_to_satoshi]
    LRD_RATES = [BitpayRates.lrd_to_satoshi]
    LSL_RATES = [BitpayRates.lsl_to_satoshi]
    LYD_RATES = [BitpayRates.lyd_to_satoshi]
    MAD_RATES = [BitpayRates.mad_to_satoshi]
    MDL_RATES = [BitpayRates.mdl_to_satoshi]
    MKD_RATES = [BitpayRates.mkd_to_satoshi]
    MMK_RATES = [BitpayRates.mmk_to_satoshi]
    MNT_RATES = [BitpayRates.mnt_to_satoshi]
    MOP_RATES = [BitpayRates.mop_to_satoshi]
    MRU_RATES = [BitpayRates.mru_to_satoshi]
    MUR_RATES = [BitpayRates.mur_to_satoshi]
    MVR_RATES = [BitpayRates.mvr_to_satoshi]
    MWK_RATES = [BitpayRates.mwk_to_satoshi]
    MYR_RATES = [BitpayRates.myr_to_satoshi]
    MZN_RATES = [BitpayRates.mzn_to_satoshi]
    NAD_RATES = [BitpayRates.nad_to_satoshi]
    NGN_RATES = [BitpayRates.ngn_to_satoshi]
    NIO_RATES = [BitpayRates.nio_to_satoshi]
    NOK_RATES = [BitpayRates.nok_to_satoshi]
    NPR_RATES = [BitpayRates.npr_to_satoshi]
    OMR_RATES = [BitpayRates.omr_to_satoshi]
    PAB_RATES = [BitpayRates.pab_to_satoshi]
    PGK_RATES = [BitpayRates.pgk_to_satoshi]
    PHP_RATES = [BitpayRates.php_to_satoshi]
    PKR_RATES = [BitpayRates.pkr_to_satoshi]
    PYG_RATES = [BitpayRates.pyg_to_satoshi]
    QAR_RATES = [BitpayRates.qar_to_satoshi]
    RON_RATES = [BitpayRates.ron_to_satoshi]
    RSD_RATES = [BitpayRates.rsd_to_satoshi]
    RWF_RATES = [BitpayRates.rwf_to_satoshi]
    SAR_RATES = [BitpayRates.sar_to_satoshi]
    SBD_RATES = [BitpayRates.sbd_to_satoshi]
    SCR_RATES = [BitpayRates.scr_to_satoshi]
    SDG_RATES = [BitpayRates.sdg_to_satoshi]
    SHP_RATES = [BitpayRates.shp_to_satoshi]
    SLL_RATES = [BitpayRates.sll_to_satoshi]
    SOS_RATES = [BitpayRates.sos_to_satoshi]
    SRD_RATES = [BitpayRates.srd_to_satoshi]
    STN_RATES = [BitpayRates.stn_to_satoshi]
    SVC_RATES = [BitpayRates.svc_to_satoshi]
    SYP_RATES = [BitpayRates.syp_to_satoshi]
    SZL_RATES = [BitpayRates.szl_to_satoshi]
    TJS_RATES = [BitpayRates.tjs_to_satoshi]
    TMT_RATES = [BitpayRates.tmt_to_satoshi]
    TND_RATES = [BitpayRates.tnd_to_satoshi]
    TOP_RATES = [BitpayRates.top_to_satoshi]
    TRY_RATES = [BitpayRates.try_to_satoshi]
    TTD_RATES = [BitpayRates.ttd_to_satoshi]
    TZS_RATES = [BitpayRates.tzs_to_satoshi]
    UAH_RATES = [BitpayRates.uah_to_satoshi]
    UGX_RATES = [BitpayRates.ugx_to_satoshi]
    UZS_RATES = [BitpayRates.uzs_to_satoshi]
    VES_RATES = [BitpayRates.ves_to_satoshi]
    VND_RATES = [BitpayRates.vnd_to_satoshi]
    VUV_RATES = [BitpayRates.vuv_to_satoshi]
    WST_RATES = [BitpayRates.wst_to_satoshi]
    XAF_RATES = [BitpayRates.xaf_to_satoshi]
    XCD_RATES = [BitpayRates.xcd_to_satoshi]
    XOF_RATES = [BitpayRates.xof_to_satoshi]
    XPF_RATES = [BitpayRates.xpf_to_satoshi]
    YER_RATES = [BitpayRates.yer_to_satoshi]
    ZAR_RATES = [BitpayRates.zar_to_satoshi]
    ZMW_RATES = [BitpayRates.zmw_to_satoshi]
    ZWL_RATES = [BitpayRates.zwl_to_satoshi]

    @classmethod
    def usd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.USD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def eur_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.EUR_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def gbp_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.GBP_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def jpy_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.JPY_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def cny_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.CNY_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def hkd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.HKD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def cad_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.CAD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def aud_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.AUD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def nzd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.NZD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def rub_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.RUB_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def brl_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.BRL_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def chf_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.CHF_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def sek_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.SEK_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def dkk_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.DKK_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def isk_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.ISK_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def pln_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.PLN_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def krw_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.KRW_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def clp_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.CLP_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def sgd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.SGD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def thb_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.THB_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def twd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.TWD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def mxn_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.MXN_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass
        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def ars_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.ARS_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def cop_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.COP_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def cup_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.CUP_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def pen_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.PEN_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def uyu_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.UYU_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def dop_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.DOP_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def bob_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.BOB_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def aed_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.AED_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def afn_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.AFN_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def all_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.ALL_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def amd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.AMD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def ang_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.ANG_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def aoa_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.AOA_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def awg_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.AWG_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def azn_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.AZN_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def bam_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.BAM_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def bbd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.BBD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def bdt_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.BDT_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def bgn_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.BGN_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def bhd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.BHD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def bif_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.BIF_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def bmd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.BMD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def bnd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.BND_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def bsd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.BSD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def btn_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.BTN_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def bwp_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.BWP_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def byn_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.BYN_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def bzd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.BZD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def cdf_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.CDF_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def clf_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.CLF_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def crc_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.CRC_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def cve_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.CVE_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def czk_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.CZK_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def djf_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.DJF_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def dzd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.DZD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def egp_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.EGP_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def etb_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.ETB_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def fjd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.FJD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def fkp_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.FKP_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def gel_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.GEL_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def ghs_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.GHS_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def gip_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.GIP_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def gmd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.GMD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def gnf_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.GNF_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def gtq_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.GTQ_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def gyd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.GYD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def hnl_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.HNL_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def hrk_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.HRK_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def htg_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.HTG_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def huf_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.HUF_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def idr_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.IDR_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def ils_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.ILS_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def inr_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.INR_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def iqd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.IQD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def irr_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.IRR_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def jmd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.JMD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def jod_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.JOD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def kes_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.KES_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def kgs_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.KGS_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def khr_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.KHR_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def kmf_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.KMF_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def kpw_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.KPW_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def kwd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.KWD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def kyd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.KYD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def kzt_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.KZT_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def lak_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.LAK_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def lbp_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.LBP_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def lkr_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.LKR_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def lrd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.LRD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def lsl_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.LSL_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def lyd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.LYD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def mad_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.MAD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def mdl_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.MDL_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def mkd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.MKD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def mmk_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.MMK_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def mnt_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.MNT_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def mop_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.MOP_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def mru_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.MRU_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def mur_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.MUR_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def mvr_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.MVR_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def mwk_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.MWK_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def myr_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.MYR_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def mzn_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.MZN_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def nad_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.NAD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def ngn_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.NGN_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def nio_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.NIO_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def nok_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.NOK_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def npr_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.NPR_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def omr_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.OMR_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def pab_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.PAB_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def pgk_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.PGK_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def php_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.PHP_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def pkr_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.PKR_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def pyg_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.PYG_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def qar_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.QAR_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def ron_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.RON_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def rsd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.RSD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def rwf_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.RWF_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def sar_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.SAR_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def sbd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.SBD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def scr_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.SCR_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def sdg_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.SDG_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def shp_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.SHP_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def sll_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.SLL_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def sos_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.SOS_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def srd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.SRD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def stn_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.STN_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def svc_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.SVC_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def syp_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.SYP_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def szl_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.SZL_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def tjs_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.TJS_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def tmt_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.TMT_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def tnd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.TND_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def top_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.TOP_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def try_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.TRY_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def ttd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.TTD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def tzs_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.TZS_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def uah_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.UAH_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def ugx_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.UGX_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def uzs_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.UZS_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def ves_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.VES_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def vnd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.VND_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def vuv_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.VUV_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def wst_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.WST_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def xaf_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.XAF_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def xcd_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.XCD_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def xof_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.XOF_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def xpf_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.XPF_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def yer_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.YER_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def zar_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.ZAR_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def zmw_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.ZMW_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def zwl_to_satoshi(cls):  # pragma: no cover

        for api_call in cls.ZWL_RATES:
            try:
                return api_call()
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")


EXCHANGE_RATES = {
    "satoshi": satoshi_to_satoshi,
    "ubch": ubch_to_satoshi,
    "mbch": mbch_to_satoshi,
    "bch": bch_to_satoshi,
    "usd": RatesAPI.usd_to_satoshi,
    "eur": RatesAPI.eur_to_satoshi,
    "gbp": RatesAPI.gbp_to_satoshi,
    "jpy": RatesAPI.jpy_to_satoshi,
    "cny": RatesAPI.cny_to_satoshi,
    "cad": RatesAPI.cad_to_satoshi,
    "aud": RatesAPI.aud_to_satoshi,
    "nzd": RatesAPI.nzd_to_satoshi,
    "rub": RatesAPI.rub_to_satoshi,
    "brl": RatesAPI.brl_to_satoshi,
    "chf": RatesAPI.chf_to_satoshi,
    "sek": RatesAPI.sek_to_satoshi,
    "dkk": RatesAPI.dkk_to_satoshi,
    "isk": RatesAPI.isk_to_satoshi,
    "pln": RatesAPI.pln_to_satoshi,
    "hkd": RatesAPI.hkd_to_satoshi,
    "krw": RatesAPI.krw_to_satoshi,
    "sgd": RatesAPI.sgd_to_satoshi,
    "thb": RatesAPI.thb_to_satoshi,
    "twd": RatesAPI.twd_to_satoshi,
    "mxn": RatesAPI.mxn_to_satoshi,
    "ars": RatesAPI.ars_to_satoshi,
    "cop": RatesAPI.cop_to_satoshi,
    "cup": RatesAPI.cup_to_satoshi,
    "uyu": RatesAPI.uyu_to_satoshi,
    "bob": RatesAPI.bob_to_satoshi,
    "pen": RatesAPI.pen_to_satoshi,
    "dop": RatesAPI.dop_to_satoshi,
    "clp": RatesAPI.clp_to_satoshi,
    "aed": RatesAPI.aed_to_satoshi,
    "afn": RatesAPI.afn_to_satoshi,
    "all": RatesAPI.all_to_satoshi,
    "amd": RatesAPI.amd_to_satoshi,
    "ang": RatesAPI.ang_to_satoshi,
    "aoa": RatesAPI.aoa_to_satoshi,
    "awg": RatesAPI.awg_to_satoshi,
    "azn": RatesAPI.azn_to_satoshi,
    "bam": RatesAPI.bam_to_satoshi,
    "bbd": RatesAPI.bbd_to_satoshi,
    "bdt": RatesAPI.bdt_to_satoshi,
    "bgn": RatesAPI.bgn_to_satoshi,
    "bhd": RatesAPI.bhd_to_satoshi,
    "bif": RatesAPI.bif_to_satoshi,
    "bmd": RatesAPI.bmd_to_satoshi,
    "bnd": RatesAPI.bnd_to_satoshi,
    "bsd": RatesAPI.bsd_to_satoshi,
    "btn": RatesAPI.btn_to_satoshi,
    "bwp": RatesAPI.bwp_to_satoshi,
    "byn": RatesAPI.byn_to_satoshi,
    "bzd": RatesAPI.bzd_to_satoshi,
    "cdf": RatesAPI.cdf_to_satoshi,
    "clf": RatesAPI.clf_to_satoshi,
    "crc": RatesAPI.crc_to_satoshi,
    "cve": RatesAPI.cve_to_satoshi,
    "czk": RatesAPI.czk_to_satoshi,
    "djf": RatesAPI.djf_to_satoshi,
    "dzd": RatesAPI.dzd_to_satoshi,
    "egp": RatesAPI.egp_to_satoshi,
    "etb": RatesAPI.etb_to_satoshi,
    "fjd": RatesAPI.fjd_to_satoshi,
    "fkp": RatesAPI.fkp_to_satoshi,
    "gel": RatesAPI.gel_to_satoshi,
    "ghs": RatesAPI.ghs_to_satoshi,
    "gip": RatesAPI.gip_to_satoshi,
    "gmd": RatesAPI.gmd_to_satoshi,
    "gnf": RatesAPI.gnf_to_satoshi,
    "gtq": RatesAPI.gtq_to_satoshi,
    "gyd": RatesAPI.gyd_to_satoshi,
    "hnl": RatesAPI.hnl_to_satoshi,
    "hrk": RatesAPI.hrk_to_satoshi,
    "htg": RatesAPI.htg_to_satoshi,
    "huf": RatesAPI.huf_to_satoshi,
    "idr": RatesAPI.idr_to_satoshi,
    "ils": RatesAPI.ils_to_satoshi,
    "inr": RatesAPI.inr_to_satoshi,
    "iqd": RatesAPI.iqd_to_satoshi,
    "irr": RatesAPI.irr_to_satoshi,
    "jmd": RatesAPI.jmd_to_satoshi,
    "jod": RatesAPI.jod_to_satoshi,
    "kes": RatesAPI.kes_to_satoshi,
    "kgs": RatesAPI.kgs_to_satoshi,
    "khr": RatesAPI.khr_to_satoshi,
    "kmf": RatesAPI.kmf_to_satoshi,
    "kpw": RatesAPI.kpw_to_satoshi,
    "kwd": RatesAPI.kwd_to_satoshi,
    "kyd": RatesAPI.kyd_to_satoshi,
    "kzt": RatesAPI.kzt_to_satoshi,
    "lak": RatesAPI.lak_to_satoshi,
    "lbp": RatesAPI.lbp_to_satoshi,
    "lkr": RatesAPI.lkr_to_satoshi,
    "lrd": RatesAPI.lrd_to_satoshi,
    "lsl": RatesAPI.lsl_to_satoshi,
    "lyd": RatesAPI.lyd_to_satoshi,
    "mad": RatesAPI.mad_to_satoshi,
    "mdl": RatesAPI.mdl_to_satoshi,
    "mkd": RatesAPI.mkd_to_satoshi,
    "mmk": RatesAPI.mmk_to_satoshi,
    "mnt": RatesAPI.mnt_to_satoshi,
    "mop": RatesAPI.mop_to_satoshi,
    "mru": RatesAPI.mru_to_satoshi,
    "mur": RatesAPI.mur_to_satoshi,
    "mvr": RatesAPI.mvr_to_satoshi,
    "mwk": RatesAPI.mwk_to_satoshi,
    "myr": RatesAPI.myr_to_satoshi,
    "mzn": RatesAPI.mzn_to_satoshi,
    "nad": RatesAPI.nad_to_satoshi,
    "ngn": RatesAPI.ngn_to_satoshi,
    "nio": RatesAPI.nio_to_satoshi,
    "nok": RatesAPI.nok_to_satoshi,
    "npr": RatesAPI.npr_to_satoshi,
    "omr": RatesAPI.omr_to_satoshi,
    "pab": RatesAPI.pab_to_satoshi,
    "pgk": RatesAPI.pgk_to_satoshi,
    "php": RatesAPI.php_to_satoshi,
    "pkr": RatesAPI.pkr_to_satoshi,
    "pyg": RatesAPI.pyg_to_satoshi,
    "qar": RatesAPI.qar_to_satoshi,
    "ron": RatesAPI.ron_to_satoshi,
    "rsd": RatesAPI.rsd_to_satoshi,
    "rwf": RatesAPI.rwf_to_satoshi,
    "sar": RatesAPI.sar_to_satoshi,
    "sbd": RatesAPI.sbd_to_satoshi,
    "scr": RatesAPI.scr_to_satoshi,
    "sdg": RatesAPI.sdg_to_satoshi,
    "shp": RatesAPI.shp_to_satoshi,
    "sll": RatesAPI.sll_to_satoshi,
    "sos": RatesAPI.sos_to_satoshi,
    "srd": RatesAPI.srd_to_satoshi,
    "stn": RatesAPI.stn_to_satoshi,
    "svc": RatesAPI.svc_to_satoshi,
    "syp": RatesAPI.syp_to_satoshi,
    "szl": RatesAPI.szl_to_satoshi,
    "tjs": RatesAPI.tjs_to_satoshi,
    "tmt": RatesAPI.tmt_to_satoshi,
    "tnd": RatesAPI.tnd_to_satoshi,
    "top": RatesAPI.top_to_satoshi,
    "try": RatesAPI.try_to_satoshi,
    "ttd": RatesAPI.ttd_to_satoshi,
    "tzs": RatesAPI.tzs_to_satoshi,
    "uah": RatesAPI.uah_to_satoshi,
    "ugx": RatesAPI.ugx_to_satoshi,
    "uzs": RatesAPI.uzs_to_satoshi,
    "ves": RatesAPI.ves_to_satoshi,
    "vnd": RatesAPI.vnd_to_satoshi,
    "vuv": RatesAPI.vuv_to_satoshi,
    "wst": RatesAPI.wst_to_satoshi,
    "xaf": RatesAPI.xaf_to_satoshi,
    "xcd": RatesAPI.xcd_to_satoshi,
    "xof": RatesAPI.xof_to_satoshi,
    "xpf": RatesAPI.xpf_to_satoshi,
    "yer": RatesAPI.yer_to_satoshi,
    "zar": RatesAPI.zar_to_satoshi,
    "zmw": RatesAPI.zmw_to_satoshi,
    "zwl": RatesAPI.zwl_to_satoshi,
}


def currency_to_satoshi(amount, currency):
    """Converts a given amount of currency to the equivalent number of
    satoshi. The amount can be either an int, float, or string as long as
    it is a valid input to :py:class:`decimal.Decimal`.

    :param amount: The quantity of currency.
    :param currency: One of the :ref:`supported currencies`.
    :type currency: ``str``
    :rtype: ``int``
    """
    satoshis = EXCHANGE_RATES[currency]()
    return int(satoshis * Decimal(amount))


class CachedRate:
    __slots__ = ("satoshis", "last_update")

    def __init__(self, satoshis, last_update):
        self.satoshis = satoshis
        self.last_update = last_update


def currency_to_satoshi_local_cache(f):
    start_time = time()

    cached_rates = dict(
        [(currency, CachedRate(None, start_time)) for currency in EXCHANGE_RATES.keys()]
    )

    @wraps(f)
    def wrapper(amount, currency):
        now = time()

        cached_rate = cached_rates[currency]

        if (
            not cached_rate.satoshis
            or now - cached_rate.last_update > DEFAULT_CACHE_TIME
        ):
            cached_rate.satoshis = EXCHANGE_RATES[currency]()
            cached_rate.last_update = now

        return int(cached_rate.satoshis * Decimal(amount))

    return wrapper


@currency_to_satoshi_local_cache
def currency_to_satoshi_local_cached():
    pass  # pragma: no cover


def currency_to_satoshi_cached(amount, currency):
    """Converts a given amount of currency to the equivalent number of
    satoshi. The amount can be either an int, float, or string as long as
    it is a valid input to :py:class:`decimal.Decimal`. Results are cached
    using a decorator for 60 seconds by default. See :ref:`cache times`.

    :param amount: The quantity of currency.
    :param currency: One of the :ref:`supported currencies`.
    :type currency: ``str``
    :rtype: ``int``
    """
    return currency_to_satoshi_local_cached(amount, currency)


def satoshi_to_currency(num, currency):
    """Converts a given number of satoshi to another currency as a formatted
    string rounded down to the proper number of decimal places.

    :param num: The number of satoshi.
    :type num: ``int``
    :param currency: One of the :ref:`supported currencies`.
    :type currency: ``str``
    :rtype: ``str``
    """
    return "{:f}".format(
        Decimal(num / Decimal(EXCHANGE_RATES[currency]()))
        .quantize(
            Decimal("0." + "0" * CURRENCY_PRECISION[currency]), rounding=ROUND_DOWN
        )
        .normalize()
    )


def satoshi_to_currency_cached(num, currency):
    """Converts a given number of satoshi to another currency as a formatted
    string rounded down to the proper number of decimal places. Results are
    cached using a decorator for 60 seconds by default. See :ref:`cache times`.

    :param num: The number of satoshi.
    :type num: ``int``
    :param currency: One of the :ref:`supported currencies`.
    :type currency: ``str``
    :rtype: ``str``
    """
    return "{:f}".format(
        Decimal(num / Decimal(currency_to_satoshi_cached(1, currency)))
        .quantize(
            Decimal("0." + "0" * CURRENCY_PRECISION[currency]), rounding=ROUND_DOWN
        )
        .normalize()
    )
