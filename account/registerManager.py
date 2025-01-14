from account.models import ReferralProfile, CustomUser
from master.models import Role, City
from .models import UserDocuments
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes, force_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from leadgenerator.settings import BASE_DIR, EMAIL_HOST_USER
from django.contrib.sites.shortcuts import get_current_site
from .utils import token_generator, render_to_pdf
from django.urls import reverse
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect
from django.contrib.auth.models import auth, Group
from django.contrib import messages
import time
from asgiref.sync import sync_to_async
import asyncio

# DATABASES_NAME = defaultdb
# DATABASES_USER = doadmin
# DATABASES_PASSWORD = AVNS_C4w1Q7b-lb0FU44li7c
# DATABASES_HOST = db-mysql-blr1-53992-do-user-12870761-0.b.db.ondigitalocean.com
# DATABASES_PORT = 25060  

# DATABASES_NAME = django-test

# DATABASES_USER = root

# DATABASES_HOST = localhost

# DATABASES_PORT = 3306

# DATABASES_PASSWORD = ""

async def async_mail_sender(email):
    print("Entered Email")
    await sync_to_async(email.send , thread_sensitive=False)(fail_silently=False)
    print("Email Sent")
    # email.send(fail_silently=False)





async def handleUserFileInputs(request , user):
    
    if not request.FILES:
        return

    # photo = request.FILES.get('identity_photo')
    # pan_card = request.FILES.get('pan_card')
    # aadhar_card = request.FILES.get('aadhar_card')
    # cancelled_cheque = request.FILES.get('cancelled_cheque')


    for file in request.FILES:
        file_content = request.FILES[file]
        filename = request.FILES[file].name
        user_document = UserDocuments(user = user , documentName = filename , document = file_content)
        await sync_to_async(user_document.save)()




def get_tenure_months(current_age, retirement_age):
    return (retirement_age - current_age) * 12


async def register_referral_logic(request):
    print(request.POST)
    start = time.time()

    group = await sync_to_async(Group.objects.get)(name="Referral Partner")
    # group = Group.objects.get(name="Referral Partner")
    fname = request.POST["fname"]
    system_role = request.POST["system_role"]
    Email = request.POST["email"]
    phone = request.POST["phone"]
    password = request.POST["password"]
    profession = request.POST["profession"]
    if profession == "Other":
        profession = request.POST["other"]
    address = request.POST["address"]
    pincode = request.POST["pincode"]
    city = request.POST["city"]
    has_gst = request.POST["has_gst"]
    reference = request.POST["reference"]
    referral_code = request.POST.get("referral_code", "")
    if await sync_to_async(CustomUser.objects.filter(email=Email).exists)():
        messages.info(request, "Email Taken")
        return redirect("register_referral")
    else:
        system_role = await sync_to_async(Role.objects.filter(role=system_role).first)()
        city = await sync_to_async(City.objects.filter(city_name=city).first)()
        print(profession)
        print(system_role)
        print(city)
        user = await sync_to_async(CustomUser.objects.create_user)(
            username="default",
            password=password,
            system_role=system_role,
            email=Email,
            phone=phone,
            address=address,
            pincode=pincode,
            city=city,
        )

        print(user)
        user.mapped_to_dept = "Admin"
        user.reporting_head = "Admin"
        user.is_active = False
        await sync_to_async(user.groups.add)(group)
        await sync_to_async(user.save)()

    referral_profile = await sync_to_async(ReferralProfile.objects.create)(
        user=user,
        full_name=fname,
        profession=profession,
        has_GST=has_gst,
        reference=reference,
        referral_code=referral_code,
    )


    await sync_to_async(referral_profile.save)()
    ini = ""
    if referral_profile.profession == "Salaried":
        ini += "SAL"
    elif referral_profile.profession == "Self Employed":
        ini += "SE"
    elif referral_profile.profession == "Freelancer":
        ini += "FL"
    elif referral_profile.profession == "Student":
        ini += "ST"
    elif referral_profile.profession == "Home Maker":
        ini += "HM"
    elif referral_profile.profession == "DSA":
        ini += "DSA"
    elif referral_profile.profession == "Insurance Agent":
        ini += "IA"
    elif referral_profile.profession == "Chartered Accountant":
        ini += "CA"
    elif referral_profile.profession == "Tax Consultants":
        ini += "TC"
    elif referral_profile.profession == "Banker":
        ini += "BNK"
    elif referral_profile.profession == "Company Secretary":
        ini += "CS"
    elif referral_profile.profession == "Real Estate Agent":
        ini += "REA"
    elif referral_profile.profession == "Builder":
        ini += "BLD"
    else:
        ini += "O"
    if user.system_role.role == "Referral Partner":
        ini += "RP"
    num = "{:04d}".format(user.id)
    newusername = ini + num
    user.username = newusername
    await sync_to_async(user.save)()
    if user.system_role.role == "Referral Partner":
        ini = "ORP"
        num = "{:03d}".format(user.id)
        newusername = ini + num
        user.username = newusername
        await sync_to_async(user.save)()
    await handleUserFileInputs(request , user)
    uidb64_pk = urlsafe_base64_encode(force_bytes(user.pk))
    uidb64_hash = urlsafe_base64_encode(force_bytes(password))
    domain = get_current_site(request).domain
    link = reverse(
        "activate",
        kwargs={
            "uidb64_pk": uidb64_pk,
            "uidb64_hash": uidb64_hash,
            "token": token_generator.make_token(user),
        },
    )
    activate_url = "http://" + domain + link
    email_body = (
        "Hi "
        + referral_profile.full_name
        + " Please use this link to verify your account\n"
        + activate_url
    )



    email = EmailMessage(
        "Activate your account",
        email_body,
        EMAIL_HOST_USER,
        [Email],
    )
    asyncio.create_task(async_mail_sender(email))
    # template = get_template('account/Agreement.html')
    context = {"partner_name": referral_profile.full_name}
    # html = template.render(context)
    pdf = render_to_pdf("account/Agreement.html", context)

    response = HttpResponse(pdf, content_type="application/pdf")
    filename = "Agreement_%s.pdf" % (user.username)

    # content = "attachment; filename='%s'" % (filename)
    response["Content-Disposition"] = 'attachment; filename="report.pdf"'
    await sync_to_async(referral_profile.agreement.save)(filename, ContentFile(pdf.content))
    print(referral_profile.agreement)
    message = "this is test mail"
    subject = "Terms and Conditions"
    mail_id = request.POST.get("email", "")
    email = EmailMessage(
        subject,
        message,
        EMAIL_HOST_USER,
        [
            mail_id,
        ],
    )
    email.content_subtype = "html"
    asyncio.create_task(async_mail_sender(email))



    print("*************")
    print(time.time() - start, " seconds took to complete...")
    print("*************")
    return redirect("email_ver_msg")

    # return referral

    


def register_vendor_logic():
    pass


def register_staff_logic():
    pass


register_manager_dict = {
    "Referral Partner": register_referral_logic,
    "Vendor": register_vendor_logic,
}
