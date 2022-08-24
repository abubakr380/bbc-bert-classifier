# from transformers import BertTokenizer

# tokenizer = BertTokenizer.from_pretrained('bert-base-cased')
#
# example_text = 'I will watch Memento tonight'
# bert_input = tokenizer(example_text,padding='max_length', max_length = 10,
#                        truncation=True, return_tensors="pt")
#
#
# print(bert_input['input_ids'])
# print(bert_input['token_type_ids'])
# print(bert_input['attention_mask'])

import pandas as pd
import numpy as np
import torch
from torch import nn
from torch.optim import Adam
from tqdm import tqdm
from bert_classifier import BertClassifier
from dataset import Dataset


def train(model, df_train_data, df_val_data, learning_rate, epochs):
    train_data, val_data = Dataset(df_train_data), Dataset(df_val_data)

    train_dataloader = torch.utils.data.DataLoader(train_data, batch_size=2, shuffle=True)
    val_dataloader = torch.utils.data.DataLoader(val_data, batch_size=2)

    use_cuda = torch.cuda.is_available()
    device = torch.device("cuda" if use_cuda else "cpu")

    criterion = nn.CrossEntropyLoss()
    optimizer = Adam(model.parameters(), lr=learning_rate)

    if use_cuda:
        model = model.cuda()
        criterion = criterion.cuda()

    for epoch_num in range(epochs):

        total_acc_train = 0
        total_loss_train = 0

        for train_input, train_label in tqdm(train_dataloader):
            train_label = train_label.to(device)
            mask = train_input['attention_mask'].to(device)
            input_id = train_input['input_ids'].squeeze(1).to(device)

            output = model(input_id, mask)

            batch_loss = criterion(output, train_label.long())
            total_loss_train += batch_loss.item()

            acc = (output.argmax(dim=1) == train_label).sum().item()
            total_acc_train += acc

            model.zero_grad()
            batch_loss.backward()
            optimizer.step()

        total_acc_val = 0
        total_loss_val = 0

        with torch.no_grad():

            for val_input, val_label in val_dataloader:
                val_label = val_label.to(device)
                mask = val_input['attention_mask'].to(device)
                input_id = val_input['input_ids'].squeeze(1).to(device)

                output = model(input_id, mask)

                batch_loss = criterion(output, val_label.long())
                total_loss_val += batch_loss.item()

                acc = (output.argmax(dim=1) == val_label).sum().item()
                total_acc_val += acc

        print(
            f'Epochs: {epoch_num + 1} | Train Loss: {total_loss_train / len(df_train_data): .3f} \
                | Train Accuracy: {total_acc_train / len(df_train_data): .3f} \
                | Val Loss: {total_loss_val / len(df_val_data): .3f} \
                | Val Accuracy: {total_acc_val / len(df_val_data): .3f}')


if __name__ == "__main__":
    dataframe = pd.read_csv('data/bbc_text.csv')
    print(dataframe.head())
    print('\n')

    np.random.seed(112)
    df_train, df_val, df_test = np.split(dataframe.sample(frac=1, random_state=42), [int(.8 * len(dataframe)), int(.9 * len(dataframe))])

    print(len(df_train), len(df_val), len(df_test))
    print('\n')

    EPOCHS = 5
    bert_model = BertClassifier()
    LR = 1e-6

    train(bert_model, df_train, df_val, LR, EPOCHS)
