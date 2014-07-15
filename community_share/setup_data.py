from community_share.models.survey import Question, SuggestedAnswer

def get_questions(creator):
    questions = [
        Question(
            text='To what extent have you worked with educators/educational institutions before?',
            creator=creator,
            question_type='signup_community_partner',
            public=True,
            only_suggested_answers=False,
            order=0,
            suggested_answers=[
                SuggestedAnswer(creator=creator,
                                text='Never'),
                SuggestedAnswer(creator=creator,
                                text='A few times'),
                SuggestedAnswer(creator=creator,
                                text='6+ times'),
                SuggestedAnswer(creator=creator,
                                text='Dozens'),
            ]
        ),
        Question(
            text='If you have worked with educators/educational institutions before, please list them here.',
            creator=creator,
            question_type='signup_community_partner',
            public=True,
            only_suggested_answers=False,
            order=1,
        ),
        Question(
            text='To what extent have you worked with community experts before?',
            creator=creator,
            question_type='signup_educator',
            public=True,
            only_suggested_answers=False,
            order=0,
            suggested_answers=[
                SuggestedAnswer(creator=creator,
                                text='Never'),
                SuggestedAnswer(creator=creator,
                                text='A few times'),
                SuggestedAnswer(creator=creator,
                                text='6+ times'),
                SuggestedAnswer(creator=creator,
                                text='Dozens'),
            ]
        ),
        Question(
            text='How did you hear about Community Share?',
            creator=creator,
            question_type='signup',
            public=False,
            only_suggested_answers=False,
            order=2,
            suggested_answers=[
                SuggestedAnswer(creator=creator,
                                text='Colleague'),
                SuggestedAnswer(creator=creator,
                                text='Friend'),
                SuggestedAnswer(creator=creator,
                                text='Media'),
                SuggestedAnswer(creator=creator,
                                text='Web search'),
            ],
        ),
        Question(
            text='Do you have any feedback that would help the educator/community partner next time they work with somebody?',
            creator=creator,
            long_answer=True,
            question_type='post_event',
            public=False,
            only_suggested_answers=False,
            requires_event_id=True,
            requires_user_id=True,
            order=1
        ),
        Question(
            text='Do you have any feedback for the Community Share administrators?',
            creator=creator,
            long_answer=True,
            question_type='post_event',
            public=False,
            only_suggested_answers=False,
            requires_event_id=True,
            order=2
        ),
    ]
    return questions
