from functools import wraps

from model import check_onboard_status, verify_char_for_user
from player_char import PlayerChar


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


def normal_build_char_id(func):
    @wraps(func)
    async def wrapper(ctx, build_type='normal', char_id=0, creation_stage=0):
        if build_type.isnumeric():
            build_type = int(build_type)
        if type(build_type) == int:

            # Replace this line with the actual check function
            enrolled, validation, stage = verify_char_for_user(ctx.author.id, char_id=build_type)
            if not enrolled:
                await ctx.send('Please enroll with !enroll command first')
                return
            if not validation:
                await ctx.send('You can only custom update your own character')
                return
            await func(ctx, build_type='normal', char_id=build_type, creation_stage=stage)
        elif build_type == 'normal':
            char_id, creation_stage = PlayerChar(ctx).fetch_latest_char_id(user_id=ctx.author.id)
            await func(ctx, build_type='normal', char_id=char_id, creation_stage=creation_stage)
        else:
            return func(ctx, build_type, 0, 0)

    return wrapper


def check_enroll(author_id):
    return check_onboard_status(author_id)
