import os
import json
import datetime
import pytz

import django
from django.db import transaction
from django.core.files import File

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iquise.settings")
django.setup()

from iquhack.models import *

HACKATHONS = ["data2020.json", "data2021.json"]
TZ = pytz.timezone("EST")

# atomic means if an error occurs at any point, we rollback
@transaction.atomic
def main(hackathon_dat_name):
    # Make sure our FAQ template is ready to go
    templates = {None: None}
    with open("faq.html", "r") as fid:
        templates["FAQ"], created = SectionTemplate.objects.get_or_create(
            name="FAQ",
            defaults={"content": fid.read().strip()},
        )

    with open(hackathon_dat_name, "r") as fid:
        dat = json.load(fid)

    hackathon_dat = dat["Hackathon"]
    if Hackathon.objects.filter(start_date__year=hackathon_dat["start_date"][0]).count():
        raise Exception("Hackathon this year already exists!")

    print "Adding hackathon...",
    # Update to appropriate python objects
    hackathon_dat["start_date"] = datetime.date(*hackathon_dat["start_date"])
    hackathon_dat["end_date"] = datetime.date(*hackathon_dat["end_date"])
    hackathon_dat["back_drop_image"] = File(open(hackathon_dat["back_drop_image"], "r"))
    hackathon_dat["opens"] = datetime.datetime(*hackathon_dat["opens"], tzinfo=TZ)
    hackathon_dat["deadline"] = datetime.datetime(*hackathon_dat["deadline"], tzinfo=TZ)
    # Add using kwarg notation
    hackathon = Hackathon(**hackathon_dat)
    hackathon.save()
    print "done"

    # Prepare tiers
    tiers_dat = {}
    for tier_dat in dat["Tier"]:
        tiers_dat[tier_dat["index"]] = tier_dat

    with open(dat["FAQs"], "r") as fid:
        faqs_dat = fid.read().strip()

    # Format of this file: {question}\n{answer; may contain \n}\n\n
    faqs_dat = faqs_dat.split("\n\n")
    print "Adding questions"
    for i, faq_dat in enumerate(faqs_dat):
        lines = faq_dat.strip().split("\n")
        question = lines[0]
        answer = "\n".join(lines[1:])  # Reassemble answer lines
        print "  %s..." % question,
        faq = FAQ(question=question, answer=answer)
        faq.save()
        UsedFAQ(hackathon=hackathon, FAQ=faq, index=i).save()
        print "done"

    print "Adding sponsors"
    for sponsor_dat in dat["Sponsor"]:
        if sponsor_dat.get("logo"):
            logo = File(open(sponsor_dat["logo"], "r"))
        else:
            logo = None
        sponsor, created = Sponsor.objects.get_or_create(
            name=sponsor_dat["name"],
            defaults = {
                "logo": logo,
                "link": sponsor_dat["link"],
            }
        ) # this also saves it
        if created:
            print "  Created sponsor " + sponsor_dat["name"]
        else:
            print "  Found sponsor " + sponsor_dat["name"]
        tier_index = sponsor_dat["tier"]
        tier, created = Tier.objects.get_or_create(
            index=tier_index,
            # defaults = tiers_dat[tier_index] # would also work (just redundant with the index)
            defaults={"logo_rel_size": tiers_dat[tier_index]["logo_rel_size"]},
        )
        if created:
            print "    Created tier %i" % tier_index
        else:
            print "    Found tier %i" % tier_index
        Sponsorship(
            hackathon=hackathon,
            sponsor=sponsor,
            tier=tier,
            platform=sponsor_dat["hardware"],
        ).save()
        print "    done."

    print "Adding sections"
    for i, section_dat in enumerate(dat["Section"]):
        content = ""
        if section_dat["content"]:
            with open(section_dat["content"], "r") as fid:
                content = fid.read().strip()
        print "  Adding %s..." % section_dat["title"],
        section = Section(
            hackathon=hackathon,
            index=i,
            title=section_dat["title"],
            content=content,
            template=templates[section_dat.get("template")], # default for get is None
        )
        section.save()
        print "done"
        for attachment in section_dat.get("attachments", []):
            print "    Addding %s..." % attachment["file"],
            Attachment(
                section=section,
                name=attachment["name"],
                file=File(open(attachment["file"], "r")),
            ).save()
            print "done"

if __name__ == "__main__":
    original_cwd = os.getcwd()
    root = os.path.dirname(__file__)
    os.chdir(os.path.join(root, ".iquhack2021_temp"))
    try:
        for hackathon_dat_name in HACKATHONS:
            main(hackathon_dat_name)
    finally:
        os.chdir(original_cwd)