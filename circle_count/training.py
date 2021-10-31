import cc_model
import data_utils as utils
from cc_model import LEARNING_RATE, MODEL_PARAMS

RERUN_EPOCHS = 100
SPARSE = False


def first_run(model_params=MODEL_PARAMS, data=utils.prepare_data(), learning_rate=LEARNING_RATE, dry_run=False):
    train_data, test_data = data

    model = cc_model.Model(model_params)
    model.build()
    model.compile(learning_rate, sparse=SPARSE)
    model.train(train_data, test_data=test_data)
    model.verify(utils.gen_circles_data(size=100))

    if not dry_run:
        model.save()

    return model


def re_run(model_params=MODEL_PARAMS, data=utils.prepare_data(), learning_rate=LEARNING_RATE, epochs=RERUN_EPOCHS):
    train_data, test_data = data

    model = cc_model.Model(model_params)
    model.load()
    model.compile(learning_rate, sparse=SPARSE)
    model.train(train_data, epochs=epochs, test_data=test_data)
    model.verify(utils.gen_circles_data(size=100))
    model.save(ask=True)

    return model


def demo_model(model_params=MODEL_PARAMS, data=utils.gen_circles_data(size=100)):
    model = cc_model.Model(model_params)
    model.load()
    model.compile(LEARNING_RATE, sparse=SPARSE)
    model.verify(data)


if __name__ == '__main__':
    # first_run()
    # first_run(dry_run=True)
    # first_run(learning_rate=0.0001)
    # first_run(dry_run=True, learning_rate=0.000001)
    re_run()
    # re_run(learning_rate=LEARNING_RATE)
    re_run(learning_rate=0.000001)
    # re_run(data=utils.prepare_error_data())
    # re_run(data=utils.prepare_error_data(), learning_rate=0.000001)
    # demo_model()
    # demo_model(data=utils.gen_circles_data(size=100))
    # demo_model(data=utils.load_sample_data(size=1000))
    # demo_model(data=utils.load_sample_error_data(size=1000))
