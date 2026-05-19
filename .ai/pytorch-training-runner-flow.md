# PytorchTrainingRunner Flow

## Cel
Ten dokument rozpisuje sam plik `src/MachineLearning/infrastructure/training/runners/pytorch_training_runner.py`:
- gdzie zaczyna się wykonanie,
- jakie metody są wołane i w jakiej kolejności,
- po co istnieje każda metoda,
- gdzie kończy się trening, a gdzie zaczyna publikacja wyniku.

## Punkt wejścia
Jedynym prawdziwym punktem wejścia do tego pliku jest metoda:

- `PytorchTrainingRunner.start(context, cancellation_token)`

To właśnie ją scheduler odpala w tle po zaakceptowaniu requestu startu treningu.

`__init__()` niczego nie trenuje. On tylko dostaje zależności i zapisuje je do pól klasy, np.:
- publisher eventów,
- loader datasetu,
- factory modelu,
- loader bazowych wag,
- writer artefaktów,
- writer raportów.

## Najprostszy model mentalny
`start()` robi 5 dużych etapów:

1. przygotuj środowisko treningu,
2. zbuduj model i dane,
3. wykonaj pętlę epok,
4. oceń najlepszy model,
5. zapisz wynik i wyślij event końcowy.

## Mermaid
```mermaid
flowchart TD
    A[start(context, cancellation_token)] --> B[_seed_everything(seed)]
    B --> C[_resolve_device()]
    C --> D[cancellation_registry.mark_running(run_name)]
    D --> E[_publish_status_changed(... TRAINING ...)]

    E --> F[model_factory.build(model_manifest)]
    F --> G[artifact_loader.load(base_model_weights)]
    G --> H{cancel requested?}
    H -->|tak| Z1[_publish_cancelled]
    H -->|nie| I[input_transform_factory.build(...)]

    I --> J[dataset_loader.load(npz)]
    J --> K[dataloader_factory.build(train/val/test)]
    K --> L[fine_tuning_policy_factory.apply(model, profile)]
    L --> M[optimizer_factory.build(profile, trainable_parameters)]
    M --> N[criterion = CrossEntropyLoss]
    N --> O[_build_scheduler(optimizer, profile)]

    O --> P[for epoch in 1..N]
    P --> Q[_train_one_epoch(... train ...)]
    Q --> R[_evaluate_loss_accuracy(... val ...)]
    R --> S[append history]
    S --> T[_write_checkpoint(epoch)]
    T --> U[_select_monitored_metrics(train, val)]
    U --> V[scheduler.step(loss) if enabled]
    V --> W{_is_monitored_metric_improved?}
    W -->|tak| X[zapisz best_model_state\nbest_epoch\n_write_best_checkpoint()]
    W -->|nie| Y[epochs_without_improvement += 1]
    X --> P2[_publish_progress(...)]
    Y --> P2[_publish_progress(...)]
    P2 --> P3{_should_stop_early?}
    P3 -->|nie| P
    P3 -->|tak| AA[break]

    AA --> AB[load_state_dict(best_model_state)]
    P3 -->|petla zakonczona| AB
    AB --> AC[_publish_status_changed(... EVALUATION ...)]
    AC --> AD[_select_evaluation_loader(test or val or train)]
    AD --> AE[_predict(model, loader, device)]
    AE --> AF[metrics_calculator.calculate(y_true, y_pred, class_names)]
    AF --> AG{cancel requested?}
    AG -->|tak| Z1
    AG -->|nie| AH[artifact_writer.write(... final model ...)]

    AH --> AI[_write_reports(...)]
    AI --> AJ[_publish_completed(...)]
    AJ --> AK[finally: cancellation_registry.release(run_name)]

    AI -->|report corrupted| AI2[ustaw report_status=corrupted]
    AI2 --> AJ
    AI -->|report write failed| AI3[ustaw report_status=missing]
    AI3 --> AJ

    Q --> ERR
    R --> ERR
    AE --> ERR
    AH --> ERR
    ERR[except Exception] --> Z2[_publish_failed(...)]
    Z2 --> AK

    Z1 --> AK
```

## Kolejność wykonania i sens metod

### 1. `start(...)`
To orkiestrator. Nie zawiera samej matematyki treningu w każdym miejscu, ale decyduje:
- co wykonać,
- w jakiej kolejności,
- kiedy publikować eventy,
- kiedy zapisać checkpoint,
- kiedy uznać model za najlepszy,
- kiedy zakończyć trening.

To jest najważniejsza metoda w pliku.

### 2. `_seed_everything(seed)`
Ustawia seedy dla:
- `random`,
- `numpy`,
- `torch`,
- `torch.cuda`.

Po co:
- żeby trening był bardziej powtarzalny,
- żeby dwa uruchomienia z tym samym seedem dawały podobne wyniki.

### 3. `_resolve_device()`
Wybiera, czy trening ma iść na:
- `cpu`,
- `cuda`,
- albo `auto`.

Po co:
- żeby runner wiedział, gdzie przenieść model i tensory.

### 4. `_publish_status_changed(...)`
Wysyła event do backendu, że trening ruszył albo przeszedł do etapu ewaluacji.

Po co:
- backend jest źródłem prawdy o stanie runu,
- UI może pokazać status `running`.

### 5. `model_factory.build(...)`
Buduje pustą architekturę sieci z manifestu.

Po co:
- runner musi najpierw stworzyć obiekt modelu PyTorch, zanim załaduje do niego wagi.

### 6. `artifact_loader.load(...)`
Ładuje bazowe wagi modelu.

Po co:
- to nie jest trening od zera,
- to jest `fine tuning` modelu bazowego.

### 7. `input_transform_factory.build(...)`
Buduje transformacje wejścia i augmentacje.

Po co:
- próbki podczas treningu mogą być modyfikowane zgodnie z profilem augmentacji,
- preprocessing musi być zgodny z typem modelu i profilem wejściowym.

### 8. `dataset_loader.load(...)`
Czyta przygotowany dataset `.npz`.

Po co:
- dostarcza surowe tablice danych i etykiety do dalszego opakowania w DataLoadery.

### 9. `dataloader_factory.build(...)`
Buduje loadery:
- `train`,
- `val`,
- `test`.

Po co:
- PyTorch trenuje najwygodniej na batchach z `DataLoader`.

### 10. `fine_tuning_policy_factory.apply(...)`
Ustala, które warstwy są trenowalne.

Po co:
- przy fine-tuningu często nie uczysz wszystkiego,
- czasem zamrażasz część warstw i odblokowujesz tylko część modelu.

### 11. `optimizer_factory.build(...)`
Tworzy optimizer.

Po co:
- optimizer aktualizuje wagi modelu po `loss.backward()`.

### 12. `_build_scheduler(...)`
Opcjonalnie tworzy scheduler learning rate.

Po co:
- gdy model przestaje się poprawiać, można obniżać learning rate.

### 13. `_train_one_epoch(...)`
To jest właściwa metoda treningowa dla jednej epoki.

W środku:
- `model.train()`
- pętla po batchach
- przeniesienie batcha na urządzenie
- `optimizer.zero_grad()`
- `logits = model(images)`
- `loss = criterion(logits, labels)`
- `loss.backward()`
- `optimizer.step()`
- zliczanie accuracy i loss

Po co:
- tu naprawdę zachodzi uczenie wag.

To jest miejsce, w którym PyTorch faktycznie „trenuje model”.

### 14. `_evaluate_loss_accuracy(...)`
Liczy stratę i accuracy bez uczenia.

W środku:
- `model.eval()`
- `torch.no_grad()`
- forward pass bez `backward`

Po co:
- sprawdzić, czy model poprawia się na zbiorze walidacyjnym.

### 15. `_select_monitored_metrics(...)`
Wybiera, co traktować jako główną metrykę do decyzji o „najlepszym modelu”.

Zasada:
- jeśli istnieje `val_loss`, to monitorujemy walidację,
- jeśli nie, fallback na train loss.

Po co:
- trzeba mieć jedno kryterium do wyboru best checkpointu.

### 16. `_is_monitored_metric_improved(...)`
Sprawdza, czy nowa epoka jest lepsza od poprzedniego best.

Po co:
- żeby zdecydować:
  - czy zapisać nowy `best_model_state`,
  - czy zaktualizować `checkpoint_best.pt`,
  - czy resetować licznik `epochs_without_improvement`.

### 17. `_write_checkpoint(...)`
Zapisuje checkpoint po każdej epoce:
- `checkpoint_epoch_1.pt`
- `checkpoint_epoch_2.pt`
- itd.

Po co:
- mieć historię postępu,
- móc debugować lub wznowić analizę.

### 18. `_write_best_checkpoint(...)`
Zapisuje najlepszy checkpoint jako:
- `checkpoint_best.pt`

Po co:
- osobno utrzymać najlepszy model, nie tylko ostatni.

### 19. `_publish_progress(...)`
Wysyła event progresu po każdej epoce.

Po co:
- backend i UI wiedzą, który to etap i jakie są metryki.

### 20. `_should_stop_early(...)`
Sprawdza, czy należy przerwać trening wcześniej.

Po co:
- nie marnować epok, jeśli model od dawna się nie poprawia.

### 21. `model.load_state_dict(best_model_state)`
Po zakończeniu pętli epok runner wraca do najlepszego zapamiętanego stanu wag.

Po co:
- finalny model ma być najlepszy, a nie po prostu ostatni.

### 22. `_select_evaluation_loader(...)`
Wybiera zbiór do końcowej ewaluacji:
- najpierw `test`,
- jeśli brak `test`, to `val`,
- jeśli brak `val`, to `train`.

Po co:
- runner potrzebuje jednego finalnego zbioru do policzenia metryk końcowych.

### 23. `_predict(...)`
Uruchamia inferencję na wybranym loaderze i zbiera:
- `y_true`,
- `y_pred`,
- średni czas inferencji.

Po co:
- potem z tego liczone są finalne metryki i raport.

### 24. `metrics_calculator.calculate(...)`
Liczy np.:
- accuracy,
- precision,
- recall,
- F1,
- confusion matrix.

Po co:
- to jest końcowa ocena modelu po treningu.

### 25. `artifact_writer.write(...)`
Zapisuje finalne wagi modelu do docelowego katalogu modelu wynikowego.

Po co:
- to jest finalny artefakt treningu, który backend później uzna za wynikowy model.

### 26. `_write_reports(...)`
Buduje `summary` i zapisuje raporty przez `TrainingReportWriter`.

Po co:
- mieć trwały opis przebiegu treningu i metryk końcowych.

### 27. `_publish_completed(...)`
Wysyła event terminalny `completed`.

Po co:
- backend dopiero po tym evencie finalizuje wpis `model.json` w rejestrze modeli.

To znaczy:
- runner kończy część ML,
- ale biznesowa „publikacja modelu” kończy się po stronie backendu.

### 28. `_publish_cancelled(...)` / `_publish_failed(...)`
Obsługa końca nieudanego:
- anulowanie przez użytkownika,
- błąd techniczny w trakcie treningu.

Po co:
- backend musi znać terminalny stan runu.

### 29. `finally -> cancellation_registry.release(run_name)`
To końcowe sprzątanie.

Po co:
- zdjąć blokadę aktywnego runu,
- pozwolić uruchomić następny trening.

## Najważniejsze rozróżnienie

### Gdzie model jest trenowany?
W praktyce głównie tutaj:
- `_train_one_epoch()`

bo tam występują:
- forward pass,
- liczenie loss,
- `backward()`,
- `optimizer.step()`.

### Gdzie runner tylko orkiestruje?
W `start()`, bo tam:
- przygotowuje zależności,
- wybiera kolejność kroków,
- publikuje eventy,
- zapisuje wyniki.

## Minimalna odpowiedź na pytanie "gdzie się co zaczyna?"

Start wykonania:
- `start(context, cancellation_token)`

Start właściwego uczenia wag:
- `_train_one_epoch(...)`

Start końcowej oceny modelu:
- `_predict(...)` i `metrics_calculator.calculate(...)`

Start zapisu wyniku:
- `artifact_writer.write(...)`

Start publikacji do reszty systemu:
- `_publish_completed(...)`

## Jednozdaniowe podsumowanie
`PytorchTrainingRunner.start()` jest dyrygentem całego procesu, a `_train_one_epoch()` jest miejscem, w którym PyTorch naprawdę uczy wagi modelu.
