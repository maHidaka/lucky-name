import itertools
import multiprocessing as mp
import sys
import csv
from collections import defaultdict


score_dict = {
1:4,2:1,3:4,4:1,5:4,6:4,7:3,8:3,9:1,10:1,11:4,12:1,13:4,14:2,15:5,16:4,17:3,18:3,19:1,20:1,21:4,22:2,23:4,24:5,25:3,26:3,27:2,28:2,29:4,30:2,31:5,32:4,33:4,34:1,35:4,36:1,37:4,38:3,39:4,40:2,41:4,42:2,43:2,44:1,45:4,46:2,47:4,48:3,49:2,50:2,51:2,52:3,53:2,54:1,55:2,56:2,57:3,58:3,59:2,60:1,61:4,62:1,63:4,64:1,65:4,66:1,67:4,68:4,69:1,70:1,71:3,72:2,73:3,74:2,75:3,76:1,77:3,78:3,79:1,80:1,81:3,82:4,83:1,84:4,85:1,86:4,87:4,88:3,89:3,90:1,91:1,92:4,93:1,94:4,95:2,96:5,97:4,98:3,99:3,100:1,101:1,102:4,103:2,104:4,105:5,106:3,107:3,108:2,109:2,110:4,111:2,112:5,113:4,114:4,115:1,116:4,117:1,118:4,119:3,120:4,121:2,122:4,123:2,124:2,125:1,126:4,127:2,128:4,129:3,130:2,131:2,132:2,133:4,134:2,135:1,136:2,137:2,138:3,139:3,140:2,141:1,142:4,143:1,144:4,145:1,146:4,147:1,148:4,149:4,150:1,151:1,152:3,153:2,154:3,155:2,156:3,157:1,158:3,159:3,160:1,161:1,162:4
}

min_stroke = 1
max_stroke = 30

# 姓・名の文字数範囲
min_len = 1
max_len = 4

# 目標スコア
min_score_all_kaku = 4 # 天格、地格、総格全て4点以上
min_score_one_is_5 = 5 # 天格、地格、総格のうち少なくとも1つは5点

def get_score(val):
    """画数からスコアを取得する"""
    return score_dict.get(val, 0)


def calculate_all_kaku(surname_strokes, givenname_strokes):
    """
    姓と名の画数タプルから、全ての格の計算画数とスコア、および総合点数を計算する
    """

    tenkaku_stroke = sum(surname_strokes)
    chikaku_stroke = sum(givenname_strokes) # 地格は名の合計画数で変更なし
    jinkaku_stroke = surname_strokes[-1] + givenname_strokes[0]

    if len(surname_strokes) == 1:
        gaikaku_left = 1
    else:
        gaikaku_left = sum(surname_strokes[:-1])


    if len(givenname_strokes) == 1:
        gaikaku_right = 1
    elif len(givenname_strokes) == 2:
        gaikaku_right = givenname_strokes[-1]
    elif len(givenname_strokes) == 3:
        gaikaku_right = sum(givenname_strokes[-2:])
    elif len(givenname_strokes) == 4: # 名が四文字の時(バグ対応)
        # 名が四文字の時は、末尾３文字ではなく末尾２文字の画数合計を使用
        gaikaku_right = sum(givenname_strokes[-2:])

    gaikaku_stroke = gaikaku_left + gaikaku_right

    shigoto_stroke = tenkaku_stroke + givenname_strokes[0]


    if len(givenname_strokes) == 4: # 名が四文字の時(バグ対応)
        # 名が四文字の時は、名の合計(地格)ではなく、最初の一文字＋末尾２文字の画数合計を使用
        katei_stroke = surname_strokes[-1] + givenname_strokes[0] + sum(givenname_strokes[-2:])
    else:
        katei_stroke = surname_strokes[-1] + chikaku_stroke

    soukaku_stroke = tenkaku_stroke + chikaku_stroke

    tenkaku_score = get_score(tenkaku_stroke)
    jinkaku_score = get_score(jinkaku_stroke)
    chikaku_score = get_score(chikaku_stroke)
    gaikaku_score = get_score(gaikaku_stroke)
    shigoto_score = get_score(shigoto_stroke)
    katei_score = get_score(katei_stroke)
    soukaku_score = get_score(soukaku_stroke)

    total_score = sum([
        tenkaku_score, jinkaku_score, chikaku_score,
        gaikaku_score, shigoto_score, katei_score, soukaku_score
    ])

    return (
        (tenkaku_stroke, jinkaku_stroke, chikaku_stroke, gaikaku_stroke, shigoto_stroke, katei_stroke, soukaku_stroke),
        (tenkaku_score, jinkaku_score, chikaku_score, gaikaku_score, shigoto_score, katei_score, soukaku_score),
        total_score
    )


def find_high_score_stroke_combinations_for_pool(surname_len, min_score):
    """
    指定文字数で、合計画数がmin_score以上のスコアを持つ組み合わせを探す
    """
    found_combinations = []
    for strokes_combo in itertools.product(range(min_stroke, max_stroke + 1), repeat=surname_len):
        total_stroke = sum(strokes_combo)
        total_score = get_score(total_stroke)
        if total_score >= min_score:
            # 画数タプル、合計画数、合計画数のスコアを格納
            found_combinations.append((strokes_combo, total_stroke, total_score))
    return found_combinations


def find_qualified_sum_combinations():
    """
    score_dictからスコア4点以上の画数を選び、重複を許して2つ選んだ和のスコアが
    全て4点以上かつ、うち1つが5点となる「(天格画数, 地格画数)ペア」を生成
    """
    # score_dictのうち、スコアが4点以上になる画数の値（キー）を収集
    high_score_strokes_for_sum = sorted([stroke for stroke, score in score_dict.items() if score >= min_score_all_kaku])

    qualified_sum_pairs = []

    # high_score_strokes_for_sum リストから重複を許して2つの値を選ぶ
    # これを天格画数、地格画数として扱う
    for tenkaku_stroke, chikaku_stroke in itertools.product(high_score_strokes_for_sum, repeat=2):

        # それぞれのスコアを取得
        tenkaku_score = get_score(tenkaku_stroke)
        chikaku_score = get_score(chikaku_stroke)

        # 総格画数とそのスコアを計算・取得
        soukaku_stroke = tenkaku_stroke + chikaku_stroke
        soukaku_score = get_score(soukaku_stroke)

        # 条件判定
        # 1. 天格、地格、総格のスコアがそれぞれ4点以上であること
        all_scores_are_min = (tenkaku_score >= min_score_all_kaku and
                              chikaku_score >= min_score_all_kaku and
                              soukaku_score >= min_score_all_kaku)

        # 2. 3つのスコアのうち、少なくとも1つが5点であること
        at_least_one_is_5 = (tenkaku_score >= min_score_one_is_5 or
                             chikaku_score >= min_score_one_is_5 or
                             soukaku_score >= min_score_one_is_5)

        # 両方の条件を満たす場合
        if all_scores_are_min and at_least_one_is_5:
            # 条件を満たす合計画数ペアと関連情報をリストに追加
            qualified_sum_pairs.append((
                (tenkaku_stroke, chikaku_stroke),
                soukaku_stroke,
                tenkaku_score,
                chikaku_score,
                soukaku_score
            ))

    return qualified_sum_pairs


def evaluate_specific_sum_combination(args):
    """
    特定の目標天格・地格画数ペアと、画数組み合わせプールを受け取り、
    該当する姓名組み合わせを全て評価し、最高の総合点数とその組み合わせを返す
    """
    (target_tenkaku_stroke, target_chikaku_stroke), high_score_stroke_combinations_pool = args

    best_score_for_sum_pair = -1
    best_combinations_for_sum_pair = [] # (姓画数タプル, 名画数タプル, 格画数タプル, 格スコアタプル, 総合点数) のリスト

    # 目標の天格画数に一致する姓の画数組み合わせをプールから抽出
    possible_surnames = [
        item for item in high_score_stroke_combinations_pool
        if item[1] == target_tenkaku_stroke # item[1] は合計画数
    ]

    # 目標の地格画数に一致する名の画数組み合わせをプールから抽出
    possible_givennames = [
        item for item in high_score_stroke_combinations_pool
        if item[1] == target_chikaku_stroke # item[1] は合計画数
    ]

    # 抽出された姓と名の全ての組み合わせを評価
    for (surname_combo, actual_tenkaku_stroke, actual_tenkaku_score), \
        (givenname_combo, actual_chikaku_stroke, actual_chikaku_score) \
        in itertools.product(possible_surnames, possible_givennames):

        # calculate_all_kaku 関数で全ての格を計算
        (kaku_strokes, kaku_scores, total_score) = calculate_all_kaku(surname_combo, givenname_combo)

        # この姓名組み合わせの総合点数が、現在の最高の総合点数を上回るかチェック
        if total_score > best_score_for_sum_pair:
            best_score_for_sum_pair = total_score
            # 組み合わせを更新
            best_combinations_for_sum_pair = [(
                surname_combo, givenname_combo,
                kaku_strokes, kaku_scores, total_score
            )]
        elif total_score == best_score_for_sum_pair:
            # 同点の場合もリストに追加
             best_combinations_for_sum_pair.append((
                surname_combo, givenname_combo,
                kaku_strokes, kaku_scores, total_score
            ))


    # この目標天格・地格画数ペアにおける、最高の総合点数と該当する組み合わせリストを返す
    return best_score_for_sum_pair, best_combinations_for_sum_pair


if __name__ == '__main__':

    print(f"姓・名の文字数{min_len}~{max_len}について、合計画数のスコアが{min_score_all_kaku}点以上になる組み合わせプールを生成します。")
    print(f"一文字の画数は{min_stroke}から{max_stroke}までです。\n")

    pool_tasks = list(range(min_len, max_len + 1))

    all_high_score_stroke_combinations_pool_raw = []
    with mp.Pool(mp.cpu_count()) as pool:
        # 各文字数について、合計画数スコア4点以上の組み合わせを並列探索
        pool_results = pool.starmap(find_high_score_stroke_combinations_for_pool,
                                    [(l, min_score_all_kaku) for l in pool_tasks])

    # 結果を一つのリストに集約
    for combinations_list in pool_results:
        all_high_score_stroke_combinations_pool_raw.extend(combinations_list)

    print(f"合計画数が{min_score_all_kaku}点以上になる画数組み合わせプールサイズ: {len(all_high_score_stroke_combinations_pool_raw)}\n")

    if not all_high_score_stroke_combinations_pool_raw:
        print("プールとなる画数組み合わせが見つかりませんでした。処理を終了します。")
        sys.exit()

    high_score_stroke_combinations_pool_indexed = defaultdict(list)
    for item in all_high_score_stroke_combinations_pool_raw:
         high_score_stroke_combinations_pool_indexed[item[1]].append(item)


    print(f"天格、地格、総格のスコアが全て{min_score_all_kaku}点以上かつ、うち1つが{min_score_one_is_5}点となる合計画数ペアを生成します。")
    qualified_sum_combinations = find_qualified_sum_combinations()

    print(f"条件を満たす合計画数ペア数: {len(qualified_sum_combinations)}\n")

    if not qualified_sum_combinations:
        print("条件を満たす天格・地格・総格の合計画数ペアが見つかりませんでした。処理を終了します。")
        sys.exit()

    print("各合計画数ペアに対して、プール内の画数組み合わせを評価します (並列実行)。")

    evaluation_tasks = []
    for sum_pair_data in qualified_sum_combinations:
        # sum_pair_data は ((天格画数, 地格画数), 総格画数, 天格スコア, 地格スコア, 総格スコア)
        target_kaku_pair = sum_pair_data[0] # (目標天格画数, 目標地格画数)
        evaluation_tasks.append((target_kaku_pair, all_high_score_stroke_combinations_pool_raw))

    print(f"評価タスク数: {len(evaluation_tasks)}")

    all_evaluation_results = [] # 各タスクからの結果 (best_score, best_combinations) のリスト
    with mp.Pool(mp.cpu_count()) as pool:
        # 並列実行
        all_evaluation_results = pool.map(evaluate_specific_sum_combination, evaluation_tasks)

    print("\n--- 評価完了 ---")

    overall_best_score = -1
    overall_best_combinations = [] # 全体で最も高い総合点数を達成した組み合わせリスト

    for best_score_for_sum_pair, best_combinations_for_sum_pair in all_evaluation_results:
        if best_score_for_sum_pair > overall_best_score:
            overall_best_score = best_score_for_sum_pair
            overall_best_combinations = best_combinations_for_sum_pair
        elif best_score_for_sum_pair == overall_best_score:
            overall_best_combinations.extend(best_combinations_for_sum_pair)

    print(f"全体の最高総合点数: {overall_best_score}")
    print(f"最高総合点数を達成した組み合わせ数: {len(overall_best_combinations)}")

    if not overall_best_combinations:
        print("最高スコアを達成する組み合わせは見つかりませんでした。")
        sys.exit()

    output_csv_path_best = 'lucky_name_list.csv'

    print(f"\n結果を '{output_csv_path_best}' に保存します...")

    try:
        with open(output_csv_path_best, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            # ヘッダー行を書き込み
            writer.writerow([
                '姓文字数', '姓画数組み合わせ',
                '名文字数', '名画数組み合わせ',
                '天格画数', '天格スコア',
                '地格画数', '地格スコア',
                '人格画数', '人格スコア',
                '外格画数', '外格スコア',
                '仕事運画数', '仕事運スコア',
                '家庭運画数', '家庭運スコア',
                '総格画数', '総格スコア',
                '総合点数'
            ])

            # 最高スコアの組み合わせデータをCSVに書き込み
            for surname_combo, givenname_combo, kaku_strokes, kaku_scores, total_score in overall_best_combinations:
                row_data = [
                    len(surname_combo),
                    str(surname_combo),
                    len(givenname_combo),
                    str(givenname_combo),
                    kaku_strokes[0], kaku_scores[0], # 天格
                    kaku_strokes[2], kaku_scores[2], # 地格 (kaku_scores[2]はchikaku_score)
                    kaku_strokes[1], kaku_scores[1], # 人格 (kaku_scores[1]はjinkaku_score)
                    kaku_strokes[3], kaku_scores[3], # 外格
                    kaku_strokes[4], kaku_scores[4], # 仕事運
                    kaku_strokes[5], kaku_scores[5], # 家庭運
                    kaku_strokes[6], kaku_scores[6], # 総格
                    total_score
                ]
                writer.writerow(row_data)

        print("保存が完了しました。")

    except IOError as e:
        print(f"ファイルの書き込み中にエラーが発生しました: {e}")
    except Exception as e:
        print(f"予期しないエラーが発生しました: {e}")