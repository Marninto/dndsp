from functools import wraps

from model import check_onboard_status


def enrolled_required(func):
    @wraps(func)
    async def wrapper(ctx, *args, **kwargs):
        # Replace this line with the actual check function
        enrolled = check_enroll(ctx.author.id)
        if not enrolled:
            await ctx.send('Please enroll with enroll command first')
            return
        await func(ctx, *args, **kwargs)
    return wrapper


def check_enroll(author_id):
    return check_onboard_status(author_id)
